import json

from fastapi import Depends
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import desc, func, select

from src.db.models import AchievementDB, StudentAchievement, StudentDB
from src.db.session import get_async_session
from src.models import Achievement, Student


class StudentDBHandler:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_student(self, student: Student) -> StudentDB | None:
        db_student = StudentDB.from_student(student)
        self.session.add(db_student)
        try:
            await self.session.commit()
            await self.session.refresh(db_student)
            return db_student
        except IntegrityError:
            await self.session.rollback()
            return None

    async def update_student(self, student: Student) -> StudentDB | None:
        db_student = await self.get_student(student.id)
        if not db_student:
            return None

        db_student.statistics = json.dumps(student.statistics)

        try:
            await self.session.commit()
            await self.session.refresh(db_student)
            return db_student
        except IntegrityError:
            await self.session.rollback()
            return None

    async def get_student(self, student_id: int) -> StudentDB | None:
        statement = select(StudentDB).where(StudentDB.id == student_id)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def delete(self, student_id: int) -> bool:
        student: StudentDB = await self.get_student(student_id)
        if not student:
            return False
        await self.session.delete(student)
        await self.session.commit()
        return True

    async def get_achievement_by_title_and_profession(self, title: str, profession: str) -> AchievementDB | None:
        statement = select(AchievementDB).where(
            (AchievementDB.title == title) & (AchievementDB.profession == profession)
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_achievement_by_student_id(self, student_id: int) -> AchievementDB | None:
        statement = (
            select(AchievementDB)
            .join(StudentAchievement)
            .where(StudentAchievement.student_id == student_id)
            .order_by(desc(StudentAchievement.created_at))
            .limit(1)
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def create_achievement(self, achievement: Achievement) -> AchievementDB:
        db_achievement = AchievementDB.from_achievement_model(achievement)
        self.session.add(db_achievement)
        await self.session.commit()
        await self.session.refresh(db_achievement)
        return db_achievement

    async def add_achievement_to_student(self, student_id: int, achievement_id: int):
        existing = await self.session.execute(
            select(StudentAchievement).where(
                (StudentAchievement.student_id == student_id) & (StudentAchievement.achievement_id == achievement_id)
            )
        )
        if existing.scalar_one_or_none() is None:
            student_achievement = StudentAchievement(student_id=student_id, achievement_id=achievement_id)
            self.session.add(student_achievement)
            await self.session.commit()

    async def get_list_of_achievements_received(self) -> list[tuple[str, str, int]]:
        """Get descending list of achievements received"""
        # Step 1: Get the IDs grouped by title
        achievement_subquery = (
            select(AchievementDB.title, AchievementDB.picture, AchievementDB.id).group_by(
                AchievementDB.title, AchievementDB.picture, AchievementDB.id
            )
        ).subquery()

        # Step 2: Count occurrences in student_achievements based on achievement ID
        statement = (
            select(
                achievement_subquery.c.title,
                achievement_subquery.c.picture,
                func.count(StudentAchievement.student_id).label("receive_count"),
            )
            .join(StudentAchievement, StudentAchievement.achievement_id == achievement_subquery.c.id)
            .group_by(achievement_subquery.c.title, achievement_subquery.c.picture)
            .order_by(func.count(StudentAchievement.student_id).desc())
        )

        result = await self.session.execute(statement)
        return result.all()


def get_student_crud(session: AsyncSession = Depends(get_async_session)) -> StudentDBHandler:
    return StudentDBHandler(session)
