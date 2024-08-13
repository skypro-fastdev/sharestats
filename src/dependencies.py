import gspread
from loguru import logger

from src.achievements import AchievementFactory, achievements_collection
from src.classes.data_cache import DataCache
from src.classes.s3 import S3Client
from src.classes.sheet_loader import SheetLoader
from src.classes.sheet_pusher import SheetPusher
from src.classes.stats_loader import StatsLoader
from src.config import IS_HEROKU, get_creds, settings

# Google Client
if IS_HEROKU:
    gclient = gspread.authorize(credentials=get_creds())
else:
    gclient = gspread.service_account(filename=settings.CREDENTIALS_PATH)

# Loader from Google Sheet
sheet_loader = SheetLoader(gclient, settings.SHEET_ID_TEST)

# Pusher to Google Sheet
sheet_pusher = SheetPusher(gclient, settings.SHEET_URL_DATA)

# Mock data cache
data_cache = DataCache()

# Statistics loader from API
stats_loader = StatsLoader(settings.LOAD_STATS_HOST, settings.LOAD_STATS_TOKEN)

# List of achievements
achievements = [AchievementFactory.create_achievement(achievement) for achievement in achievements_collection]

# S3 client
s3_client = S3Client(
    key_id=settings.YANDEX_S3_KEY_ID, secret_key=settings.YANDEX_S3_SECRET_KEY, bucket=settings.YANDEX_S3_BUCKET
)


def load_cache():
    logger.info("Loading mock data cache...")
    sheet_loader.get_spreadsheet()
    data_cache.update_stats(sheet_loader.get_data_from_sheet("mock"))
    data_cache.update_courses(sheet_loader.get_data_from_sheet("courses"))
    data_cache.update_skills(sheet_loader.get_data_from_sheet("skills"))
    logger.info("Data cache has been loaded!")
