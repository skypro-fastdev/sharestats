from datetime import datetime
from random import choice

from fastapi import HTTPException
from pydantic import ValidationError

from src.models import ProfessionEnum, Student
from src.utils import async_generate_image, check_achievements, get_user_stats


class StudentHandler:
    def __init__(self, student_id: int):
        self.student_id = student_id
        self.student = None
        self.achievements = None
        self.achievement = None

    async def initialize(self):
        stats = await get_user_stats(self.student_id)
        if not stats:
            raise HTTPException(status_code=404, detail=f"Студент с id {self.student_id} не найден")

        try:
            profession_str = stats.get("profession", "NA")
            profession_enum = ProfessionEnum.from_str(profession_str)

            started_at = datetime.strptime(stats.get("started_at"), "%d.%m.%Y").date()

            self.student = Student(
                id=self.student_id,
                first_name=stats.get("first_name", "Name"),
                last_name=stats.get("last_name", "Surname"),
                profession=profession_enum,
                started_at=started_at,
                statistics=stats,
            )
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=e.errors()) from e

        self.achievements = check_achievements(self.student)
        self.achievement = self.get_random_achievement()

    def get_random_achievement(self):
        return choice(self.achievements[1:]) if len(self.achievements) > 1 else self.achievements[0]

    async def gen_image(self, platform: str) -> dict:
        """Generate image with achievement"""
        return await async_generate_image(self.achievement, platform)


async def get_student_handler(student_id: int) -> StudentHandler:
    handler = StudentHandler(student_id)
    await handler.initialize()
    return handler
