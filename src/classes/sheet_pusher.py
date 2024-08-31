import asyncio
from datetime import datetime
from typing import Any

from gspread import Client, Worksheet
from loguru import logger

from src.models import CRMSubmission, URLSubmission


class SheetPusher:
    def __init__(self, g_client, sheet_id):
        self.__google_client: Client = g_client
        self.__sheet_id: str = sheet_id
        self.__worksheets: dict[str, Worksheet] = {}
        self.__failed_submissions: dict[str, list[list[str | Any]]] = {
            "shared": [],
            "requested_cc": [],
            "requested_course": [],
        }
        self.__retry_tasks: dict[str, asyncio.Task] = {}
        self.__lock = asyncio.Lock()

    @staticmethod
    def __get_current_time() -> str:
        return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    def __get_worksheet(self, worksheet_name: str) -> Worksheet:
        if worksheet_name not in self.__worksheets:
            self.__worksheets[worksheet_name] = self.__google_client.open_by_key(self.__sheet_id).worksheet(
                worksheet_name
            )
        return self.__worksheets[worksheet_name]

    async def push_data_to_sheet(self, data: URLSubmission | CRMSubmission, worksheet_name: str):
        try:
            return await asyncio.to_thread(self._sync_push_data_to_sheet, data, worksheet_name)
        except Exception as e:
            logger.error(f"Error submitting data to sheet '{worksheet_name}': {e}")
            return False

    def _sync_push_data_to_sheet(self, data: URLSubmission | CRMSubmission, worksheet_name: str):
        try:
            worksheet: Worksheet = self.__get_worksheet(worksheet_name)

            data_dict = data.model_dump()
            if isinstance(data, CRMSubmission):  # удаляем ненужно поле перед записью в таблицу
                del data_dict["order"]

            data_to_push = [self.__get_current_time()] + list(data_dict.values())
            result = worksheet.append_row(data_to_push)

            if result.get("updates", {}).get("updatedRows", 0) == 1:
                logger.info(f"Data successfully submitted to Google Sheet '{worksheet_name}'")
                return True

            logger.warning(f"Unexpected result from Google Sheets API for '{worksheet_name}': {result}")
            return False
        except Exception as e:
            logger.error(f"Error submitting data to sheet '{worksheet_name}': {e}")
            return False

    async def save_failed_submission(self, data: URLSubmission | CRMSubmission, worksheet_name: str):
        async with self.__lock:
            data_dict = data.model_dump()
            if isinstance(data, CRMSubmission):  # удаляем ненужно поле перед записью в таблицу
                del data_dict["order"]

            failed_data = [self.__get_current_time()] + list(data_dict.values())
            self.__failed_submissions[worksheet_name].append(failed_data)

            if worksheet_name not in self.__retry_tasks or self.__retry_tasks[worksheet_name].done():
                self.__retry_tasks[worksheet_name] = asyncio.create_task(self.retry_failed_submissions(worksheet_name))

    async def retry_failed_submissions(self, worksheet_name: str):
        while self.__failed_submissions[worksheet_name]:
            await asyncio.sleep(60)
            async with self.__lock:
                batch = self.__failed_submissions[worksheet_name][:100]  # Process in batches of 100
                self.__failed_submissions[worksheet_name] = self.__failed_submissions[worksheet_name][100:]

            worksheet: Worksheet = self.__get_worksheet(worksheet_name)
            try:
                result = worksheet.append_rows(batch)
                if result.get("updates", {}).get("updatedRows", 0) == len(batch):
                    logger.info(f"Successfully retried {len(batch)} failed submissions for '{worksheet_name}'")
                else:
                    logger.warning(f"Unexpected result when retrying submissions for '{worksheet_name}': {result}")
                    self.__failed_submissions[worksheet_name].extend(batch)
            except Exception as e:
                logger.error(f"Failed to retry submissions for '{worksheet_name}': {e}")
                self.__failed_submissions[worksheet_name].extend(batch)

        logger.info(f"All failed submissions processed for '{worksheet_name}'")
