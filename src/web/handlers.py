from random import choice

from fastapi import HTTPException
from pydantic import ValidationError

from src.models import Student
from src.utils import check_achievements, generate_image, get_user_stats


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
            self.student = Student(
                id=self.student_id,
                first_name=stats.get("first_name", "Name"),
                last_name=stats.get("last_name", "Surname"),
                statistics=stats,
            )
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=e.errors()) from e

        self.achievements = check_achievements(self.student)
        self.achievement = self.get_random_achievement()

    def get_random_achievement(self):
        return choice(self.achievements[1:]) if len(self.achievements) > 1 else self.achievements[0]

    def gen_image(self):
        return generate_image(self.achievement)


async def get_student_handler(student_id: int) -> StudentHandler:
    handler = StudentHandler(student_id)
    await handler.initialize()
    return handler
