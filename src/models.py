from enum import Enum
from typing import Callable

from pydantic import BaseModel


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
