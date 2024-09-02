from datetime import date, datetime
from enum import Enum
from typing import Annotated, Callable

from pydantic import AfterValidator, BaseModel, Field, computed_field, field_validator
from pydantic_core import ValidationError


def plural_text(n: int, month: bool = False) -> str:
    word = ["месяц", "месяца", "месяцев"] if month else ["день", "дня", "дней"]
    if n % 10 == 1 and n % 100 != 11:
        return f"{n} {word[0]}"
    elif 2 <= n % 10 <= 4 and (n % 100 < 10 or n % 100 >= 20):  # noqa RET505
        return f"{n} {word[1]}"
    else:
        return f"{n} {word[2]}"


class AchievementType(str, Enum):
    NEWBIE = "newbie"
    CHILLY = "chilly"
    DETERMINED = "determined"
    LURKY = "lurky"
    POPCORN = "popcorn"
    NIGHT_OWL = "nightowl"
    SUNSHINE = "sunshine"
    NO_REST = "norest"
    LIGHTNING = "lightning"
    FLAWLESS = "flawless"
    LIVEWATCHER = "livewatcher"
    QUESTIONCAT = "questioncat"
    RESPONSIVE = "responsive"
    SHERIFF = "sheriff"
    PERSONAL = "personal"
    LASTMINUTE = "lastminute"


class ProfessionEnum(str, Enum):
    PD = "Python-разработчик"
    DA = "аналитик данных"
    GD = "графический дизайнер"
    WD = "веб-разрабтчик"
    QA = "инженер по тестированию"
    JD = "Java-разработчик"
    IM = "интернет-маркетолог"
    PM = "менеджер проектов"
    NA = "..."

    @classmethod
    def from_str(cls, name: str):
        if name in cls.__members__:
            return cls.__members__[name]
        return cls.NA

    @property
    def dative(self):
        dative_forms = {
            self.PD: "Python-разработке",
            self.DA: "аналитике данных",
            self.GD: "графическому дизайну",
            self.WD: "веб-разработке",
            self.QA: "тестированию",
            self.JD: "Java-разработке",
            self.IM: "интернет-маркетингу",
            self.PM: "менеджменту проектов",
            self.NA: "...",
        }
        return dative_forms[self]


class Achievement(BaseModel):
    title: str
    description: str
    type: AchievementType
    profession: str | None = None
    get_description: Callable[[dict[str, int | str]], str] | None = None
    conditions: Callable[[dict[str, int | str]], bool] | None = None
    picture: str = ""


class Student(BaseModel):
    id: int
    first_name: str | None = None
    last_name: str | None = None
    profession: ProfessionEnum
    started_at: date
    statistics: dict[str, int | str]
    meme_stats: dict[str, str] = {}
    achievements: list[Achievement] = []
    points: int = 0
    last_login: datetime | None = None

    @computed_field
    def days_since_start(self) -> str:
        days = (date.today() - self.started_at).days
        return plural_text(days)

    @computed_field
    def months_since_start(self) -> str:
        days = (date.today() - self.started_at).days
        return plural_text(round(days / 30), month=True)

    @computed_field
    def profession_info(self) -> str:
        from src.dependencies import data_cache

        return data_cache.professions_info.get(self.profession.name, "")

    @field_validator("statistics")
    def check_required_keys(cls, data_dict):  # noqa N805
        required_keys = {
            "program",
            "started_at",
            "lessons_in_program",
            "lessons_completed",
            "homework_total",
            "homework_intime",
            "homework_firstday",
            "homework_night",
            "homework_morning",
            "homework_weekend",
            "homework_last_6",
            "courseworks_in_program",
            "courseworks_completed",
            "questions_number",
            "comments_help",
            "lives_total",
            "lives_visited",
            "lives_watched_in_record",
            "ik_spent",
            "rates_created",
        }
        missing_keys = required_keys - set(data_dict.keys())
        if missing_keys:
            raise ValidationError(f"Не хватает ключей {missing_keys} в статистике студента {data_dict['id']}")
        return data_dict


class URLSubmission(BaseModel):
    student_id: int
    student_name: str
    student_profession: str
    url: str


class CRMSubmission(BaseModel):
    student_id: int
    phone: str | None = None
    order: str | None = None


class Challenge(BaseModel):
    id: str
    title: str
    eval: str
    value: int
    is_active: bool = Annotated[str, AfterValidator(lambda value: value == "TRUE")]


class Product(BaseModel):
    id: str
    title: str
    value: int
    is_active: bool = Annotated[str, AfterValidator(lambda value: value == "TRUE")]


class Meme(BaseModel):
    id: str
    group: str
    question: str
    options: list[str]

    @field_validator("options", mode="before")
    @classmethod
    def split_options(cls, v):
        if isinstance(v, str):
            return v.split("\n")
        return v


class Purchase(BaseModel):
    product_id: str
    student_id: int
    created_at: datetime = Field(default_factory=datetime.now)


class DateQuery(BaseModel):
    search_date: date | None = Field(
        None, validation_alias="date", description="Date for which to fetch login data (YYYY-MM-DD)"
    )

    @field_validator("search_date")
    @classmethod
    def check_date(cls, v):
        if v is None:
            return datetime.now().date()
        if isinstance(v, date):
            return v
        try:
            return datetime.strptime(v, "%Y-%m-%d").date()
        except ValueError:
            return datetime.now().date()

    @property
    def formatted_date(self) -> str:
        return self.search_date.strftime("%Y-%m-%d")
