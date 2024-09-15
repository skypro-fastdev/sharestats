import json
from datetime import date, datetime
from typing import Sequence

from fastapi import Depends
from sqlalchemy import Row
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlmodel import desc, func, select

from src.db.models import AchievementDB, StudentAchievement, StudentChallenge, StudentDB
from src.db.session import get_async_session
from src.models import Achievement, Student


class StudentDBHandler:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_student(self, student: Student) -> StudentDB | None:
        try:
            db_student = StudentDB.from_student(student)
            self.session.add(db_student)
            await self.session.commit()
            await self.session.refresh(db_student)
            return db_student
        except IntegrityError:
            await self.session.rollback()
            return None

    async def update_student(self, student: Student, bonuses_visited: bool = False) -> StudentDB | None:
        db_student = await self.get_student(student.id)
        if not db_student:
            return None

        try:
            db_student.first_name = student.first_name
            db_student.last_name = student.last_name
            db_student.profession = student.profession
            db_student.statistics = json.dumps(student.statistics, ensure_ascii=False)

            if bonuses_visited:
                db_student.bonuses_last_visited = datetime.now()
            else:
                db_student.last_login = datetime.now()

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

    async def get_students_with_last_login(self, target_date: date) -> Sequence[Row]:
        statement = select(StudentDB.id, StudentDB.last_login).where(func.date(StudentDB.last_login) == target_date)
        result = await self.session.execute(statement)
        return result.all()

    async def get_student_with_challenges(self, student_id: int) -> StudentDB | None:
        statement = (
            select(StudentDB)
            .options(joinedload(StudentDB.student_challenges).joinedload(StudentChallenge.challenge))
            .where(StudentDB.id == student_id)
        )
        result = await self.session.execute(statement)
        return result.unique().scalar_one_or_none()

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
        result = await self.session.execute(
            select(StudentAchievement).where(
                (StudentAchievement.student_id == student_id) & (StudentAchievement.achievement_id == achievement_id)
            )
        )
        existing_achievement = result.scalar_one_or_none()
        if existing_achievement:
            # Update timestamp for existing achievement
            existing_achievement.created_at = datetime.now()
            await self.session.commit()
            return

        if existing_achievement is None:
            student_achievement = StudentAchievement(student_id=student_id, achievement_id=achievement_id)
            self.session.add(student_achievement)
            await self.session.commit()

    async def get_list_of_achievements_received(self) -> Sequence[Row]:
        """Get descending list of achievements received"""
        # Step 1: Get the unique achievement titles, pictures and ids
        achievement_subquery = (
            select(AchievementDB.title, AchievementDB.picture, AchievementDB.id).distinct().subquery()
        )

        # Step 2: Count occurrences in student_achievements based on achievement ID
        statement = (
            select(
                achievement_subquery.c.title,
                achievement_subquery.c.picture,
                func.count(StudentAchievement.student_id).label("receive_count"),
            )
            .select_from(achievement_subquery)
            .join(StudentAchievement, StudentAchievement.achievement_id == achievement_subquery.c.id)
            .group_by(achievement_subquery.c.title, achievement_subquery.c.picture)
            .order_by(func.count(StudentAchievement.student_id).desc())
        )

        result = await self.session.execute(statement)
        return result.all()

    async def add_meme_stats_to_student(self, student_id: int, memes: dict) -> StudentDB | None:
        db_student = await self.get_student(student_id)

        if not db_student:
            return None

        try:
            db_student.meme_stats = json.dumps(memes, ensure_ascii=False)
            await self.session.commit()
            await self.session.refresh(db_student)
            return db_student
        except IntegrityError:
            await self.session.rollback()
            return None


def get_student_crud(session: AsyncSession = Depends(get_async_session)) -> StudentDBHandler:
    return StudentDBHandler(session)
