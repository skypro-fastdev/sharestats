import asyncio

from gspread import Client, Spreadsheet, Worksheet
from loguru import logger


class SheetLoader:
    def __init__(self, g_client, sheet_id):
        self.__google_client: Client = g_client
        self.__sheet_id: str = sheet_id
        self.__spreadsheet: Spreadsheet | None = None

    def get_spreadsheet(self):
        try:
            self.__spreadsheet = self.__google_client.open_by_key(self.__sheet_id)
        except Exception as e:
            logger.error(f"Error loading spreadsheet: {e}")

    def get_data_from_sheet(self, sheet_name: str):
        try:
            worksheet: Worksheet = self.__spreadsheet.worksheet(sheet_name)
            return worksheet.get_all_values()
        except Exception as e:
            logger.error(f"Error loading data from sheet with name: {sheet_name}: {e}")
            return []


class AsyncSheetLoaderWrapper:
    def __init__(self, sheet_loader: SheetLoader):
        self.__sheet_loader = sheet_loader

    async def get_spreadsheet(self):
        return await asyncio.to_thread(self.__sheet_loader.get_spreadsheet)

    async def get_data_from_sheet(self, sheet_name: str):
        return await asyncio.to_thread(self.__sheet_loader.get_data_from_sheet, sheet_name)
