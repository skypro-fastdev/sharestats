import aiohttp
from aiogram.types import BufferedInputFile
from loguru import logger

from src.bot.client import bot
from src.config import settings


async def send_telegram_updates(image_url: str, referal_url: str):
    """Отправка изображения в телеграм-канал Skypro Sharestats"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                if response.status == 200:
                    image_data = await response.read()
                    filename = image_url.split("/")[-1]

                    await bot.send_photo(settings.CHANNEL_ID, BufferedInputFile(image_data, filename=filename))
                    await bot.send_message(settings.CHANNEL_ID, referal_url)
                else:
                    logger.error(f"Failed to download image: HTTP {response.status}")
    except Exception as e:
        logger.error(f"Error while downloading image ({image_url}) and sending it to Telegram channel.\n{e}")
