from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, update

from src.db.models import ChallengesDB
from src.models import Challenge


class ChallengeCRUD:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_challenge(self, challenge_id: str) -> ChallengesDB | None:
        result = await self.session.execute(select(ChallengesDB).where(ChallengesDB.id == challenge_id))
        return result.scalar_one_or_none()

    async def get_all_challenges(self, active_only: bool = False) -> list[ChallengesDB]:
        query = select(ChallengesDB)
        if active_only:
            query = query.where(ChallengesDB.is_active == True)  # noqa
        result = await self.session.execute(query)
        return result.scalars().all()

    async def create_challenge(self, challenge: Challenge) -> ChallengesDB | None:
        try:
            db_challenge = ChallengesDB(**challenge.model_dump())
            self.session.add(db_challenge)
            await self.session.commit()
            await self.session.refresh(db_challenge)
            logger.info(f"Created challenge {db_challenge.id}")
            return db_challenge
        except Exception as e:
            logger.error(f"Failed to create challenge: {e}")
            await self.session.rollback()
            return None

    async def update_challenge(self, challenge: Challenge) -> ChallengesDB | None:
        db_challenge = await self.get_challenge(challenge.id)
        if not db_challenge:
            return None

        try:
            for key, value in challenge.model_dump().items():
                setattr(db_challenge, key, value)

            await self.session.commit()
            await self.session.refresh(db_challenge)
            logger.info(f"Updated challenge {db_challenge.id}")
            return db_challenge
        except Exception as e:
            logger.error(f"Failed to update challenge {db_challenge.id}: {e}")
            await self.session.rollback()
            return None

    async def deactivate_challenge(self, challenge_id: str) -> None:
        try:
            await self.session.execute(
                update(ChallengesDB).where(ChallengesDB.id == challenge_id).values(is_active=False)
            )
            await self.session.commit()
            logger.info(f"Deactivated challenge {challenge_id}")
        except Exception as e:
            logger.error(f"Failed to deactivate challenge {challenge_id}: {e}")
            await self.session.rollback()

    async def sync_challenges(self, data_cache: dict[str, Challenge]) -> None:
        db_challenges = await self.get_all_challenges()
        db_challenge_ids = {challenge.id for challenge in db_challenges}

        challenges_updated = 0
        challenges_created = 0
        challenges_deactivated = 0

        # Update or create challenges
        for challenge_id, challenge in data_cache.items():
            if challenge_id in db_challenge_ids:
                if not data_cache[challenge_id].is_active:
                    await self.deactivate_challenge(challenge_id)
                    challenges_deactivated += 1
                    continue
                await self.update_challenge(challenge)
                challenges_updated += 1
            elif data_cache[challenge_id].is_active:
                await self.create_challenge(challenge)
                challenges_created += 1

        # Deactivate inactive challenges
        for db_challenge in db_challenges:
            if db_challenge.id not in data_cache and db_challenge.is_active:
                await self.deactivate_challenge(db_challenge.id)
                logger.info(f"Challenge {db_challenge.id} deactivated in DB")
                challenges_deactivated += 1

        logger.info(
            f"Synced challenges: {challenges_updated} updated, "
            f"{challenges_created} created, "
            f"{challenges_deactivated} deactivated"
        )


async def get_challenge_crud(session: AsyncSession) -> ChallengeCRUD:
    return ChallengeCRUD(session)
