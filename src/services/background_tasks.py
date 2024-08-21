import asyncio

from loguru import logger

from src.classes.data_cache import DataCache
from src.classes.sheet_loader import SheetLoader
from src.db.challenges_crud import get_challenge_crud
from src.db.session import get_async_session


async def update_challenges_periodically(
    cafeteria_loader: SheetLoader,
    data_cache: DataCache,
):
    while True:
        try:
            logger.info("Updating challenges from Google Sheets...")
            cafeteria_loader.get_spreadsheet()
            data_cache.update_challenges(cafeteria_loader.get_data_from_sheet("challenges"))

            async for session in get_async_session():
                crud = await get_challenge_crud(session)
                if data_cache.challenges:
                    await crud.sync_challenges(data_cache.challenges)

                await crud.update_student_challenges()
                break

            logger.info("Challenges update completed successfully.")
        except Exception as e:
            logger.error(f"Error during challenges update: {e}")

        await asyncio.sleep(60)  # 30 seconds
