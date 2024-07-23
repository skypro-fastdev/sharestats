import gspread

from src.achievements import AchievementFactory, achievements_collection
from src.classes.sheet_loader import SheetLoader
from src.classes.stats_loader import StatsLoader
from src.config import settings

# Google Client
gclient = gspread.service_account(filename=settings.CREDENTIALS_PATH)

# Loader from Google Sheet
sheet_loader = SheetLoader(gclient, settings.SHEET_ID_TEST)

# Statistics loader from API
stats_loader = StatsLoader(settings.LOAD_STATS_HOST, settings.LOAD_STATS_TOKEN)

# List of achievements
achievements = [AchievementFactory.create_achievement(achievement) for achievement in achievements_collection]
