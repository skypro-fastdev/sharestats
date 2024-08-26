from datetime import datetime
from random import choice

from fastapi import HTTPException
from loguru import logger
from pydantic import ValidationError

from src.models import Achievement, AchievementType, ProfessionEnum, Student
from src.services.stats import check_achievements, get_user_stats


class StudentHandler:
    def __init__(self, student_id: int):
        self.student_id = student_id
        self.student: Student | None = None
        self.achievements = None
        self.achievement = None

    async def initialize(self) -> None:
        stats = await get_user_stats(self.student_id)
        if not stats:
            logger.warning(f"No stats found for student_id: {self.student_id}")
            return

        try:
            profession_str = stats.get("profession", "NA")
            profession_enum = ProfessionEnum.from_str(profession_str)

            started_at = datetime.strptime(stats.get("started_at"), "%d.%m.%Y").date()
            full_name = stats.get("student_name", "")
            try:
                last_name = full_name.split(" ")[0]
                first_name = full_name.split(" ")[1]
            except IndexError:
                first_name, last_name = full_name, ""

            self.student = Student(
                id=self.student_id,
                first_name=first_name,
                last_name=last_name,
                profession=profession_enum,
                started_at=started_at,
                statistics=stats,
            )
        except ValidationError as e:
            logger.error(f"Failed to initialize student handler! student_id: {self.student_id}")
            raise HTTPException(status_code=400, detail=e.errors()) from e

        self.achievements = check_achievements(self.student)
        self.achievement = self.get_random_achievement()

    def get_random_achievement(self) -> Achievement:
        """Return random achievement, prioritizing non-basic achievements"""
        basic_achievements = (AchievementType.CHILLY, AchievementType.DETERMINED, AchievementType.LURKY)

        non_basic_achievements = [a for a in self.achievements if a.type not in basic_achievements]

        if non_basic_achievements:
            return choice(non_basic_achievements)

        # Если есть только базовые достижения, выбираем случайное из них
        basic_achievements_list = [a for a in self.achievements if a.type in basic_achievements]

        if basic_achievements_list:
            return choice(basic_achievements_list)

        return Achievement(
            type=AchievementType.CHILLY,
            title="На чиле",
            description="Наслаждаюсь новым статусом ученика, не сомневаюсь в своих силах, "
            "знаю что все легко изучу и сделаю",
            picture="chilly.png",
            profession=self.student.profession.name,
        )


async def get_student_handler(student_id: int) -> StudentHandler:
    handler = StudentHandler(student_id)
    await handler.initialize()
    return handler
