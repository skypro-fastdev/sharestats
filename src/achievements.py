from abc import ABC, abstractmethod

from src.models import Achievement, AchievementType


class AchievementBase(ABC):
    type: AchievementType
    title: str

    @abstractmethod
    def check(self, stats: dict[str, int | str]) -> bool:
        pass

    @abstractmethod
    def describe(self, stats: dict[str, int | str]) -> str:
        pass


class NewbieAchievement(AchievementBase):
    type = AchievementType.NEWBIE
    title = "Новичок"

    def check(self, stats: dict[str, int | str]) -> bool:
        return True

    def describe(self, stats: dict[str, int | str]) -> str:
        return "У нас еще мало данных,\nчтобы вычислить ваш стиль"


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

    def describe(self, stats: dict[str, int | str]) -> str:
        return "Я смотрю все\nзанятия в записи"


class NightOwlAchievement(AchievementBase):
    type = AchievementType.NIGHT_OWL
    title = "Неспящий"

    def check(self, stats: dict[str, int | str]) -> bool:
        homework_total = stats.get("homework_total")
        homework_night = stats.get("homework_night")

        if not all([homework_total, homework_night]):
            return False

        return homework_total > 3 and homework_night / homework_total > 0.5

    def describe(self, stats: dict[str, int | str]) -> str:
        return "Большинство моих домашек\nсданы ночью"


class SunshineAchievement(AchievementBase):
    type = AchievementType.SUNSHINE
    title = "Солнышко"

    @staticmethod
    def _get_stats(stats: dict[str, int | str]) -> tuple[int | None, int | None]:
        homework_total = stats.get("homework_total")
        homework_morning = stats.get("homework_morning")

        if not all([homework_total, homework_morning]):
            return None, None

        return homework_total, homework_morning

    def check(self, stats: dict[str, int | str]) -> bool:
        homework_total, homework_morning = self._get_stats(stats)

        if not homework_total:
            return False

        return homework_total > 3 and homework_morning / homework_total > 0.5

    def describe(self, stats: dict[str, int | str]) -> str:
        return "Я учусь  утром, пока все\nна работе или спят\n"


"""
    def describe(self, stats: dict[str, int | str]) -> str:
        homework_total, homework_morning = self._get_stats(stats)

        return (f"Я учусь  утром, пока все\nна работе или спят\n"
                f"{homework_morning} из {homework_total} домашек сданы утром")
"""


class NoRestAchievement(AchievementBase):
    type = AchievementType.NO_REST
    title = "Без выходных"

    @staticmethod
    def _get_stats(stats: dict[str, int | str]) -> tuple[int | None, int | None]:
        homework_total = stats.get("homework_total")
        homework_weekend = stats.get("homework_weekend")

        if not all([homework_total, homework_weekend]):
            return None, None

        return homework_total, homework_weekend

    def check(self, stats: dict[str, int | str]) -> bool:
        homework_total, homework_weekend = self._get_stats(stats)

        if not homework_total:
            return False

        return homework_total > 3 and homework_weekend / homework_total > 0.5

    def describe(self, stats: dict[str, int | str]) -> str:
        return "Пока все отдыхают,\nя решаю задачки"


achievements_collection: list[AchievementBase] = [
    NewbieAchievement(),
    PopcornAchievement(),
    NightOwlAchievement(),
    SunshineAchievement(),
    NoRestAchievement(),
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
