from src.bot.client import bot
from src.config import settings


async def send_telegram_updates(referal_url: str, image_url: str):
    """Отправка изображения в телеграм-канал Skypro Sharestats"""
    await bot.send_photo(settings.CHANNEL_ID, photo=image_url)
    await bot.send_message(settings.CHANNEL_ID, referal_url)
