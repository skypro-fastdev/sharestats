from abc import ABC, abstractmethod

from src.models import Achievement, AchievementType


class AchievementBase(ABC):
    type: AchievementType
    title: str

    @abstractmethod
    def check(self, stats: dict[str, int | str]) -> bool:
        pass

    @abstractmethod
    def describe(self, prof: str) -> str:
        pass


class NewbieAchievement(AchievementBase):
    type = AchievementType.NEWBIE
    title = "Новичок"

    def check(self, stats: dict[str, int | str]) -> bool:
        return True

    def describe(self, prof: str) -> str:
        return "У нас еще мало данных, чтобы вычислить ваш стиль"


class PopcornAchievement(AchievementBase):
    type = AchievementType.POPCORN
    title = "С попкорном"

    def check(self, stats: dict[str, int | str]) -> bool:
        lives_total = stats.get("lives_total")
        lives_visited = stats.get("lives_visited")
        lives_watched_in_record = stats.get("lives_watched_in_record")

        if not lives_total or not lives_watched_in_record:
            return False

        return lives_total > 3 and lives_visited == 0 and lives_total - lives_watched_in_record <= 5

    def describe(self, prof: str) -> str:
        return "Люблю смотреть занятия, но в записи в удобное время."


class NightOwlAchievement(AchievementBase):
    type = AchievementType.NIGHT_OWL
    title = "Неспящий"

    def check(self, stats: dict[str, int | str]) -> bool:
        homework_total = stats.get("homework_total")
        homework_night = stats.get("homework_night")

        if not all([homework_total, homework_night]):
            return False

        return homework_total > 3 and homework_night / homework_total > 0.5

    def describe(self, prof: str) -> str:
        return f"Сдаю домашки по {prof} ночью, пока все спят!"


class SunshineAchievement(AchievementBase):
    type = AchievementType.SUNSHINE
    title = "Солнышко"

    def check(self, stats: dict[str, int | str]) -> bool:
        homework_total = stats.get("homework_total")
        homework_morning = stats.get("homework_morning")

        if not all([homework_total, homework_morning]):
            return False

        return homework_total > 3 and homework_morning / homework_total > 0.5

    def describe(self, prof: str) -> str:
        return f"Сдаю домашки по {prof} по утрам"


class NoRestAchievement(AchievementBase):
    type = AchievementType.NO_REST
    title = "Без выходных"

    def check(self, stats: dict[str, int | str]) -> bool:
        homework_total = stats.get("homework_total")
        homework_weekend = stats.get("homework_weekend")

        if not all([homework_total, homework_weekend]):
            return False

        return homework_total > 3 and homework_weekend / homework_total > 0.5

    def describe(self, prof: str) -> str:
        return f"Сдаю домашки по {prof} даже на выходных, пока все отдыхают"


class LightningAchievement(AchievementBase):
    type = AchievementType.LIGHTNING
    title = "Молния"

    def check(self, stats: dict[str, int | str]) -> bool:
        homework_total = stats.get("homework_total")
        homework_firstday = stats.get("homework_firstday")

        if not all([homework_total, homework_firstday]):
            return False

        return homework_total > 3 and homework_firstday / homework_total > 0.3

    def describe(self, prof: str) -> str:
        return f"Сдаю домашки по {prof} в первые 24 часа"


class FlawlessAchievement(AchievementBase):
    type = AchievementType.FLAWLESS
    title = "Безупречный"

    def check(self, stats: dict[str, int | str]) -> bool:
        homework_total = stats.get("homework_total")
        homework_intime = stats.get("homework_intime")

        if not all([homework_total, homework_intime]):
            return False

        return 3 < homework_total == homework_intime

    def describe(self, prof: str) -> str:
        return f"100% моих домашек по {prof} сданы вовремя"


class LivewatcherAchievement(AchievementBase):
    type = AchievementType.LIVEWATCHER
    title = "Внимательный зритель"

    def check(self, stats: dict[str, int | str]) -> bool:
        lives_total = stats.get("lives_total")
        lives_visited = stats.get("lives_visited")

        if not all([lives_total, lives_visited]):
            return False

        return lives_visited > 3 and lives_visited / lives_total > 0.5

    def describe(self, prof: str) -> str:
        return f"Активно участвую в онлайн-занятиях по {prof}"


class QuestionCatAchievement(AchievementBase):
    type = AchievementType.QUESTIONCAT
    title = "Кот вопроскин"

    def check(self, stats: dict[str, int | str]) -> bool:
        questions_number = stats.get("questions_number")

        if not questions_number:
            return False

        return questions_number > 7

    def describe(self, prof: str) -> str:
        return f"Я задаю вопросы, как только что-то не понятно в {prof}"


class ResponsiveAchievement(AchievementBase):
    type = AchievementType.RESPONSIVE
    title = "Отзывчивый"

    def check(self, stats: dict[str, int | str]) -> bool:
        comments_help = stats.get("comments_help")

        if not comments_help:
            return False

        return comments_help > 3

    def describe(self, prof: str) -> str:
        return f"Я помогаю другим ученикам разбираться с их вопросами по {prof}"


class SheriffAchievement(AchievementBase):
    type = AchievementType.SHERIFF
    title = "Новый шериф"

    def check(self, stats: dict[str, int | str]) -> bool:
        homework_total = stats.get("homework_total")
        rates_created = stats.get("rates_created")

        if not all([homework_total, rates_created]):
            return False

        return homework_total > 3 and rates_created / homework_total > 0.5

    def describe(self, prof: str) -> str:
        return f"Проставляю оценки наставникам, материалам и занятиям по {prof}"


class PersonalAchievement(AchievementBase):
    type = AchievementType.PERSONAL
    title = "Персональный"

    def check(self, stats: dict[str, int | str]) -> bool:
        ik_spent = stats.get("ik_spent")

        if not ik_spent:
            return False

        return ik_spent > 5

    def describe(self, prof: str) -> str:
        return f"Я часто заависаю на личных встречах с наставниками по {prof}"


achievements_collection: list[AchievementBase] = [
    NewbieAchievement(),
    PopcornAchievement(),
    NightOwlAchievement(),
    SunshineAchievement(),
    NoRestAchievement(),
    LightningAchievement(),
    FlawlessAchievement(),
    LivewatcherAchievement(),
    QuestionCatAchievement(),
    ResponsiveAchievement(),
    SheriffAchievement(),
    PersonalAchievement(),
]


class AchievementFactory:
    """Фабрика для создания достижений"""

    @staticmethod
    def create_achievement(achievement: AchievementBase) -> Achievement:
        picture_path = f"{achievement.type.value}.png"
        return Achievement(
            type=achievement.type,
            title=achievement.title,
            description="",
            get_description=achievement.describe,
            conditions=achievement.check,
            picture=picture_path,
        )
