import asyncio
from datetime import datetime

from gspread import Client, Worksheet
from loguru import logger

from src.models import URLSubmission


class SheetPusher:
    def __init__(self, g_client, sheet_id):
        self.__google_client: Client = g_client
        self.__sheet_id: str = sheet_id
        self.__worksheet: Worksheet | None = None
        self.__failed_submissions: list[list[str]] = []
        self.__retry_task = None
        self.__lock = asyncio.Lock()

    @staticmethod
    def __get_current_time() -> str:
        return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    def __get_worksheet(self):
        if not self.__worksheet:
            self.__worksheet = self.__google_client.open_by_key(self.__sheet_id).get_worksheet(0)
        return self.__worksheet

    async def push_data_to_sheet(self, data: URLSubmission):
        try:
            return await asyncio.to_thread(self._sync_push_data_to_sheet, data)
        except Exception as e:
            logger.error(f"Error submitting URL and student data to sheet: {e}")
            return False

    def _sync_push_data_to_sheet(self, data: URLSubmission):
        try:
            worksheet: Worksheet = self.__get_worksheet()
            data_to_push = [self.__get_current_time()] + list(data.model_dump().values())
            result = worksheet.append_row(data_to_push)

            if result.get("updates", {}).get("updatedRows", 0) == 1:
                logger.info(f"Student {data.student_id} data successfully submitted to Google Sheet")
                return True

            logger.warning(f"Unexpected result from Google Sheets API: {result}")
            return False
        except Exception as e:
            logger.error(f"Error submitting URL and student data to sheet: {e}")
            return False

    async def save_failed_submission(self, data: URLSubmission):
        async with self.__lock:
            failed_data = [self.__get_current_time()] + list(data.model_dump().values())
            self.__failed_submissions.append(failed_data)
            if self.__retry_task is None or self.__retry_task.done():
                self.__retry_task = asyncio.create_task(self.retry_failed_submissions())

    async def retry_failed_submissions(self):
        while self.__failed_submissions:
            await asyncio.sleep(60)
            async with self.__lock:
                batch = self.__failed_submissions[:100]  # Process in batches of 100
                self.__failed_submissions = self.__failed_submissions[100:]

            worksheet: Worksheet = self.__get_worksheet()
            try:
                result = worksheet.append_rows(batch)
                if result.get("updates", {}).get("updatedRows", 0) == len(batch):
                    logger.info(f"Successfully retried {len(batch)} failed submissions")
                else:
                    logger.warning(f"Unexpected result when retrying submissions: {result}")
                    self.__failed_submissions.extend(batch)
            except Exception as e:
                logger.error(f"Failed to retry submissions: {e}")
                self.__failed_submissions.extend(batch)

        logger.info("All failed submissions processed")
