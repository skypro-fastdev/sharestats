import asyncio

from aiogram import Bot
from loguru import logger

from src.bot.client import bot
from src.config import settings


class TelegramLogger:
    def __init__(self, tg_bot: Bot, check_interval=5):
        self.__bot = tg_bot
        self.__chat_id: str = settings.ADMIN_CHANNEL_ID
        self.__queue: asyncio.Queue = asyncio.Queue()
        self.check_interval: int = check_interval
        asyncio.create_task(self.sender())

    async def sender(self):
        while True:
            await asyncio.sleep(self.check_interval)
            messages = []
            while not self.__queue.empty():
                try:
                    messages.append(self.__queue.get_nowait())
                    self.__queue.task_done()
                except asyncio.QueueEmpty:
                    break

            if messages:
                await self.__send_messages_to_channel(messages)

    async def __send_messages_to_channel(self, messages: list[dict[str, str]]):
        try:
            batch_text = "\n\n".join([self.format_log_entry(msg) for msg in messages])
            await self.__bot.send_message(chat_id=self.__chat_id, text=batch_text)
        except Exception as e:
            logger.error(f"Failed to send log messages: {e}")

    async def log(self, level: str, message: str):
        if level in ["WARNING", "ERROR"]:
            await self.__queue.put({"level": level, "message": message})

    @staticmethod
    def format_log_entry(log_entry: dict[str, str]) -> str:
        level = log_entry["level"]
        message = log_entry["message"]
        emoji = "🔴" if level == "ERROR" else "🟠"
        return f"{emoji} {level}\n{message}"


tg_logger = TelegramLogger(bot)
