import asyncio

from loguru import logger

from src.classes.data_cache import DataCache
from src.classes.sheet_loader import AsyncSheetLoaderWrapper, SheetLoader
from src.classes.stats_loader import StatsLoader
from src.db.challenges_crud import ChallengeDBHandler
from src.db.session import get_async_session
from src.db.students_crud import StudentDBHandler


async def get_challenges_and_products_data(cafeteria_loader: SheetLoader) -> tuple:
    async_sheet_loader = AsyncSheetLoaderWrapper(cafeteria_loader)
    await async_sheet_loader.get_spreadsheet()
    challenges_data = await async_sheet_loader.get_data_from_sheet("challenges")
    products_data = await async_sheet_loader.get_data_from_sheet("products")
    return challenges_data, products_data


async def get_memes_data(data_loader: SheetLoader) -> list:
    async_sheet_loader = AsyncSheetLoaderWrapper(data_loader)
    await async_sheet_loader.get_spreadsheet()
    return await async_sheet_loader.get_data_from_sheet("memes")


# async def update_challenges_statistics_periodically(
#     # cafeteria_loader: SheetLoader,
#     data_cache: DataCache,
#     stats_loader: StatsLoader,
# ) -> None:
#     while True:
#         try:
#             # logger.info("Updating challenges and products from Google Sheet...")
#             # challenges, products = await get_challenges_and_products_data(cafeteria_loader)
#             # data_cache.update_challenges(challenges)
#             # data_cache.update_products(products)
#
#             async for session in get_async_session():
#                 student_crud = StudentDBHandler(session)
#                 # Update student stats from Yandex Lambda function to the database
#                 await student_crud.update_students_stats(data_cache, stats_loader, batch_size=10)
#                 break
#
#                 # Sync challenges from Google Sheets to the database
#                 # challenge_crud = ChallengeDBHandler(session)
#                 # if data_cache.challenges:
#                 #     await challenge_crud.sync_challenges(data_cache.challenges)
#
#                 # Sync products from Google Sheets to the database
#                 # products_crud = ProductDBHandler(session)
#                 # if data_cache.products:
#                 #     await products_crud.sync_products(data_cache.products)
#
#             async for session in get_async_session():
#                 challenge_crud = ChallengeDBHandler(session)
#                 # Check if students have completed challenges and add points to them
#                 await challenge_crud.update_all_students_challenges()
#                 logger.info("Challenges updates for students completed.")
#                 break
#
#             # logger.info("Challenges and products updates completed.")
#         except Exception as e:
#             logger.error(f"Error during students challenges update: {e}")
#
#         await asyncio.sleep(20 * 60)  # 20 minutes


async def update_meme_data_periodically(
    data_loader: SheetLoader,
    data_cache: DataCache,
) -> None:
    while True:
        try:
            logger.info("Updating meme data from Google Sheet...")
            meme_data = await get_memes_data(data_loader)
            data_cache.update_meme_data(meme_data)

            for key, value in data_cache.meme_data.items():
                logger.info(f"Options for {key}: {len(value.options)}")

            logger.info("Meme's data updated.")
        except Exception as e:
            logger.error(f"Error during meme's data update: {e}")

        await asyncio.sleep(60 * 60)  # 60 minutes
