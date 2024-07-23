from enum import Enum
from typing import Callable

from pydantic import BaseModel, field_validator
from pydantic_core import ValidationError


class AchievementType(str, Enum):
    NEWBIE = "newbie"
    POPCORN = "popcorn"
    NIGHT_OWL = "nightowl"
    SUNSHINE = "sunshine"
    NO_REST = "norest"


class Achievement(BaseModel):
    title: str
    description: str
    type: AchievementType
    get_description: Callable[[dict[str, int | str]], str]  # функция генерации описания по стате в некоторых ачивках
    conditions: Callable[[dict[str, int | str]], bool]  # функция проверки получения ачивки
    picture: str = ""


class Student(BaseModel):
    id: int
    first_name: str | None = None
    last_name: str | None = None
    statistics: dict[str, int | str]
    achievements: list[Achievement] = []

    @field_validator("statistics")
    def check_required_keys(cls, data_dict):  # noqa N805
        required_keys = {
            "program",
            "lessons_in_program",
            "lessons_completed",
            "homework_total",
            "homework_intime",
            "homework_firstday",
            "homework_night",
            "homework_morning",
            "homework_weekend",
            "courseworks_in_program",
            "courseworks_completed",
            "questions_number",
            "comments_help",
            "lives_total",
            "lives_visited",
            "lives_watched_in_record",
        }
        missing_keys = required_keys - set(data_dict.keys())
        if missing_keys:
            raise ValidationError(f"Не хватает ключей {missing_keys} в статистике студента {data_dict['id']}")
        return data_dict
