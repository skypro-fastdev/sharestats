import asyncio

from loguru import logger

from src.classes.data_cache import DataCache
from src.classes.sheet_loader import SheetLoader, AsyncSheetLoaderWrapper
from src.classes.stats_loader import StatsLoader
from src.db.challenges_crud import get_challenge_crud
from src.db.students_crud import StudentDBHandler
from src.db.session import get_async_session


async def get_challenges_data(cafeteria_loader: SheetLoader) -> list:
    async_sheet_loader = AsyncSheetLoaderWrapper(cafeteria_loader)
    await async_sheet_loader.get_spreadsheet()
    challenges_data = await async_sheet_loader.get_data_from_sheet("challenges")
    return challenges_data


async def update_challenges_periodically(
    cafeteria_loader: SheetLoader,
    data_cache: DataCache,
    stats_loader: StatsLoader,
):
    while True:
        try:
            logger.info("Updating challenges from Google Sheets...")
            challenges_data = await get_challenges_data(cafeteria_loader)
            data_cache.update_challenges(challenges_data)

            async for session in get_async_session():
                student_crud = StudentDBHandler(session)
                # Update student stats from Yandex Lambda function to the database
                await student_crud.update_students_stats(data_cache, stats_loader, batch_size=10)

                # Sync challenges from Google Sheets to the database
                challenge_crud = await get_challenge_crud(session)
                if data_cache.challenges:
                    await challenge_crud.sync_challenges(data_cache.challenges)

                # Check if students have completed challenges and add points to them
                await challenge_crud.update_student_challenges()
                break

            logger.info("Challenges update completed successfully.")
        except Exception as e:
            logger.error(f"Error during challenges update: {e}")

        await asyncio.sleep(60)  # 60 seconds
