from aiogram.types import FSInputFile

from src.bot.client import bot
from src.config import settings


async def send_telegram_updates(referal_url: str, image_path: str):
    """Отправка изображения в телеграм-канал Skypro Sharestats"""
    image_to_channel = FSInputFile(f"data/{image_path}")

    await bot.send_photo(settings.CHANNEL_ID, photo=image_to_channel)
    await bot.send_message(settings.CHANNEL_ID, referal_url)
