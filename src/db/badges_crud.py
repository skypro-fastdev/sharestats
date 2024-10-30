from fastapi import Depends
from loguru import logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import BadgeDB
from src.db.session import get_async_session
from src.models import Badge


class BadgeDBHandler:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_badge_by_id(self, id_: int) -> BadgeDB | None:
        try:
            return await self.session.get(BadgeDB, id_)
        except Exception as e:
            logger.error(f"Failed to get badge by id: {e}")

    async def process_badges_batch(self, badges: list[Badge]):
        try:
            await self.session.execute(text("TRUNCATE TABLE badges"))
            new_badges = [BadgeDB(**badge.model_dump()) for badge in badges]
            self.session.add_all(new_badges)
            await self.session.commit()
        except Exception as e:
            logger.error(f"Failed to process badges: {e}")
            await self.session.rollback()


async def get_badges_crud(session: AsyncSession = Depends(get_async_session)) -> BadgeDBHandler:
    return BadgeDBHandler(session)
