import json

from fastapi import Depends
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlmodel import not_, or_, select

from src.db.models import ChallengesDB, StudentChallenge, StudentDB
from src.db.session import get_async_session
from src.models import Challenge
from src.services.safe_eval import safe_eval_condition


class ChallengeDBHandler:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_challenge(self, challenge_id: str) -> ChallengesDB | None:
        result = await self.session.execute(select(ChallengesDB).where(ChallengesDB.id == challenge_id))
        return result.scalar_one_or_none()

    async def get_all_challenges(
        self, active_only: bool = False, profession: str | None = None, exclude_ids: list = None
    ) -> list[ChallengesDB]:
        query = select(ChallengesDB)

        if active_only:
            query = query.where(ChallengesDB.is_active == True)  # noqa

        if profession:
            query = query.where(or_(ChallengesDB.profession == profession, ChallengesDB.profession == "ALL"))

        if exclude_ids:
            query = query.where(not_(ChallengesDB.id.in_(exclude_ids)))

        result = await self.session.execute(query)
        return list(result.scalars().all())

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

    async def process_challenges_batch(self, challenges: list[Challenge]) -> dict:
        results = {"created": 0, "updated": 0, "unchanged": 0, "failed": 0}

        for challenge in challenges:
            try:
                existing_challenge = await self.get_challenge(challenge.id)

                if existing_challenge is None:
                    new_challenge = await self.create_challenge(challenge)
                    if new_challenge:
                        results["created"] += 1
                    else:
                        results["failed"] += 1
                elif (
                    existing_challenge.is_active != challenge.is_active
                    or existing_challenge.title != challenge.title
                    or existing_challenge.eval != challenge.eval
                    or existing_challenge.value != challenge.value
                ):
                    updated_challenge = await self.update_challenge(challenge)
                    if updated_challenge:
                        results["updated"] += 1
                    else:
                        results["failed"] += 1
                else:
                    results["unchanged"] += 1
            except Exception as e:
                logger.error(f"Failed to process challenge {challenge.id}: {e}")
                results["failed"] += 1

        return results

    async def get_students_with_challenges(self) -> list[StudentDB]:
        # Получаем всех студентов с их текущими челленджами
        statement = select(StudentDB).options(joinedload(StudentDB.student_challenges))
        students = await self.session.execute(statement)
        return list(students.unique().scalars().all())

    async def update_student_challenges(
        self, student: StudentDB, student_challenges: list[ChallengesDB]
    ) -> tuple[list[ChallengesDB], list[ChallengesDB]]:
        student_stats = json.loads(student.statistics)
        completed_challenges_ids = [c.id for c in student_challenges] if student_challenges else []

        available_challenges = await self.get_all_challenges(
            active_only=True, profession=student.profession.name, exclude_ids=completed_challenges_ids
        )

        total_points_earned = 0
        new_completed_challenges = []

        for challenge in available_challenges:
            try:
                if safe_eval_condition(challenge.eval, student_stats):
                    new_challenge = StudentChallenge(student_id=student.id, challenge_id=challenge.id)
                    self.session.add(new_challenge)
                    total_points_earned += challenge.value
                    new_completed_challenges.append(challenge)
                    logger.info(
                        f"Student {student.id} completed challenge {challenge.id} and earned {challenge.value} points"
                    )
            except ValueError as e:
                logger.error(f"Error evaluating challenge {challenge.id} for student {student.id}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error for challenge {challenge.id} and student {student.id}: {e}")

        if new_completed_challenges:
            try:
                student.points += total_points_earned
                await self.session.commit()
                logger.info(
                    f"Added {len(new_completed_challenges)} new challenges for student {student.id}. "
                    f"Total points earned: {total_points_earned}"
                )
            except Exception as e:
                logger.error(f"Failed to update student {student.id} points: {e}")
                await self.session.rollback()

        total_completed_challenges = student_challenges + new_completed_challenges
        updated_available_challenges = [
            challenge for challenge in available_challenges if challenge not in new_completed_challenges
        ]

        return updated_available_challenges, total_completed_challenges


async def get_challenge_crud(session: AsyncSession = Depends(get_async_session)) -> ChallengeDBHandler:
    return ChallengeDBHandler(session)
