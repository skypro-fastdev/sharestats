from aiogram import Bot, Dispatcher

from src.config import settings

bot = Bot(settings.TG_TOKEN)
dp = Dispatcher()
