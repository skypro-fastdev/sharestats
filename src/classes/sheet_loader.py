from gspread import Client, Spreadsheet, Worksheet
from loguru import logger


class SheetLoader:
    def __init__(self, g_client, sheet_id):
        self.__google_client: Client = g_client
        self.__sheet_id: str = sheet_id

    def get_all_rows(self, worksheet_name: str | None = None):
        try:
            sheet: Spreadsheet = self.__google_client.open_by_key(self.__sheet_id)
            if worksheet_name:
                worksheet: Worksheet = sheet.worksheet(worksheet_name)
            else:
                worksheet: Worksheet = sheet.get_worksheet(0)
            return worksheet.get_all_values()
        except Exception as e:
            logger.error(f"Ошибка при попытке получить данные из тестовой таблицы: {e}")
