import asyncio

from loguru import logger

from src.classes.data_cache import DataCache
from src.classes.sheet_loader import AsyncSheetLoaderWrapper, SheetLoader


async def get_data_from_sheet(data_loader: SheetLoader, sheet_name: str) -> list:
    async_sheet_loader = AsyncSheetLoaderWrapper(data_loader)
    await async_sheet_loader.get_spreadsheet()
    return await async_sheet_loader.get_data_from_sheet(sheet_name)


async def update_meme_data_periodically(
    data_loader: SheetLoader,
    data_cache: DataCache,
) -> None:
    while True:
        try:
            logger.info("Updating meme data from Google Sheet...")
            meme_data = await get_data_from_sheet(data_loader, "memes")
            data_cache.update_meme_data(meme_data)

            for key, value in data_cache.meme_data.items():
                logger.info(f"Options for {key}: {len(value.options)}")

            logger.info("Meme's data updated.")
        except Exception as e:
            logger.error(f"Error during meme's data update: {e}")

        await asyncio.sleep(60 * 60)  # 60 minutes
