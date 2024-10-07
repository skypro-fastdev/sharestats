import json
from datetime import date, datetime

from loguru import logger
from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint

from src.models import Achievement, AchievementType, ProfessionEnum, ProfessionEnumWithAll, Student, plural_text


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
    points: int = 0
    meme_stats: str = Field(default="{}")
    last_login: datetime | None = None
    bonuses_last_visited: datetime | None = None

    student_achievements: list["StudentAchievement"] = Relationship(back_populates="student")
    student_challenges: list["StudentChallenge"] = Relationship(back_populates="student")
    student_products: list["StudentProduct"] = Relationship(back_populates="student")

    @property
    def days_since_start(self) -> str:
        days = (date.today() - self.started_at).days
        return plural_text(days)

    def to_student(self) -> Student | None:
        try:
            return Student(
                id=self.id,
                first_name=self.first_name,
                last_name=self.last_name,
                profession=self.profession,
                started_at=self.started_at,
                statistics=json.loads(self.statistics),
                meme_stats=json.loads(self.meme_stats),
                points=self.points,
                last_login=self.last_login,
                bonuses_last_visited=self.bonuses_last_visited,
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
            meme_stats=json.dumps(student.meme_stats),
            points=student.points,
            last_login=student.last_login,
            bonuses_last_visited=student.bonuses_last_visited,
        )


class StudentChallenge(SQLModel, table=True):
    __tablename__ = "student_challenges"
    __table_args__ = (UniqueConstraint("student_id", "challenge_id"),)

    id: int | None = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="students.id")
    challenge_id: str = Field(foreign_key="challenges.id")

    student: StudentDB = Relationship(back_populates="student_challenges")
    challenge: "ChallengesDB" = Relationship(back_populates="student_challenges")


class ChallengesDB(SQLModel, table=True):
    __tablename__ = "challenges"
    id: str = Field(default=None, primary_key=True)
    title: str
    profession: ProfessionEnumWithAll | None = Field(default=None)
    eval: str
    value: int
    is_active: bool

    student_challenges: list["StudentChallenge"] = Relationship(back_populates="challenge")


class StudentProduct(SQLModel, table=True):
    __tablename__ = "student_products"

    id: int | None = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="students.id")
    product_id: str = Field(foreign_key="products.id")
    added_by: str
    created_at: datetime = Field(default_factory=datetime.now, index=True)

    student: StudentDB = Relationship(back_populates="student_products")
    product: "ProductDB" = Relationship(back_populates="student_products")


class ProductDB(SQLModel, table=True):
    __tablename__ = "products"
    id: str = Field(default=None, primary_key=True)
    title: str
    description: str | None = None
    value: int
    is_active: bool

    student_products: list["StudentProduct"] = Relationship(back_populates="product")


class BadgeDB(SQLModel, table=True):
    __tablename__ = "badges"

    id: int | None = Field(default=None, primary_key=True)
    badge_type: str
    student_id: int
    student_name: str
    title: str
    description: str
