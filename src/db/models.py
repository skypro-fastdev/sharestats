import json
from datetime import date, datetime

from loguru import logger
from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint

from src.models import Achievement, AchievementType, ProfessionEnum, Student, plural_days


class StudentAchievement(SQLModel, table=True):
    __tablename__ = "student_achievements"
    student_id: int = Field(foreign_key="students.id", primary_key=True)
    achievement_id: int = Field(foreign_key="achievements.id", primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now, index=True)

    student: "StudentDB" = Relationship(back_populates="student_achievements")
    achievement: "AchievementDB" = Relationship(back_populates="student_achievements")


class AchievementDB(SQLModel, table=True):
    __tablename__ = "achievements"
    __table_args__ = (UniqueConstraint("title", "profession"),)

    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    type: AchievementType
    description: str
    profession: str = Field(index=True)
    picture: str  # путь к картинке в папке images/

    student_achievements: list["StudentAchievement"] = Relationship(back_populates="achievement")

    def to_achievement_model(self) -> Achievement | None:
        try:
            return Achievement(
                title=self.title,
                description=self.description,
                profession=self.profession,
                picture=self.picture,
                type=self.type,
            )
        except Exception as e:
            logger.error(f"Failed to convert achievement data from db to model: {e}")
            return None

    @classmethod
    def from_achievement_model(cls, achievement: Achievement) -> "AchievementDB":
        return cls(
            title=achievement.title,
            description=achievement.description,
            profession=achievement.profession,
            picture=achievement.picture,
            type=achievement.type,
        )


class StudentDB(SQLModel, table=True):
    __tablename__ = "students"
    id: int | None = Field(default=None, primary_key=True)
    first_name: str | None = None
    last_name: str | None = None
    profession: ProfessionEnum
    started_at: date
    statistics: str = Field(default="{}")

    student_achievements: list["StudentAchievement"] = Relationship(back_populates="student")

    @property
    def days_since_start(self) -> str:
        days = (date.today() - self.started_at).days
        return plural_days(days)

    def to_student(self) -> Student | None:
        try:
            return Student(
                id=self.id,
                first_name=self.first_name,
                last_name=self.last_name,
                profession=self.profession,
                started_at=self.started_at,
                statistics=json.loads(self.statistics),
            )
        except Exception as e:
            logger.error(f"Failed to convert student data from db to model: {e}")
            return None

    @classmethod
    def from_student(cls, student: Student) -> "StudentDB":
        return cls(
            id=student.id,
            first_name=student.first_name,
            last_name=student.last_name,
            profession=student.profession,
            started_at=student.started_at,
            statistics=json.dumps(student.statistics),
        )
