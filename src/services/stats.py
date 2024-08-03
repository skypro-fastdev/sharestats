from typing import Any

from loguru import logger

from src.dependencies import achievements, data_cache, stats_loader
from src.models import Achievement, Student


async def get_user_stats(student_id: int) -> dict[str, Any]:
    """Получаем статистику студента"""
    if str(student_id).startswith("999"):  # моковые данные для тестов
        return data_cache.stats.get(student_id, {})
    stats = await stats_loader.get_stats(student_id)
    return {k: v for k, v in stats.items() if v is not None}


def check_achievements(student: Student) -> list[Achievement]:
    """Проверка достижений"""
    achieved = []
    try:
        for a in achievements:
            if a.conditions(student.statistics):
                a.description = a.get_description(student.profession.dative)
                a.profession = student.profession.name
                achieved.append(a)
    except Exception as e:
        logger.error(f"Ошибка при проверке достижений: {e}")
        achieved.append(achievements[0])
    return achieved


def plural_variant(n: int, type_: str) -> str:
    """Форматирование множественного числа"""
    match type_:
        case "homework":
            text = ["домашка", "домашки", "домашек"]
        case "question":
            text = ["вопрос", "вопроса", "вопросов"]
        case _:
            return str(n)
    if n % 10 == 1 and n % 100 != 11:
        return f"{n} {text[0]}"
    elif 2 <= n % 10 <= 4 and (n % 100 < 10 or n % 100 >= 20):  # noqa RET505
        return f"{n} {text[1]}"
    else:
        return f"{n} {text[2]}"


def get_stats(student: Student) -> dict:
    """Получаем результаты студента для страницы со всей статистикой"""
    stats = student.statistics

    def safe_get(key):
        value = stats.get(key, None)
        return value if value is not None else "?"

    lessons_in_program = safe_get("lessons_in_program")
    lessons_completed = safe_get("lessons_completed")

    if isinstance(lessons_in_program, int) and isinstance(lessons_completed, int):
        percent_of_lessons_completed = round((lessons_completed / lessons_in_program) * 100)
    else:
        percent_of_lessons_completed = "? "

    return {
        "percent_of_lessons_completed": percent_of_lessons_completed,
        "lessons_completed": f"{lessons_completed} / {lessons_in_program}",
        "courseworks_completed": f"{safe_get("courseworks_completed")} / {safe_get("courseworks_in_program")}",
        "lives_visited": safe_get("lives_visited"),
        "lives_watched_in_record": safe_get("lives_watched_in_record"),
        "homework_morning": plural_variant(safe_get("homework_morning"), "homework"),
        "homework_night": plural_variant(safe_get("homework_night"), "homework"),
        "homework_weekend": plural_variant(safe_get("homework_weekend"), "homework"),
        "homework_intime": plural_variant(safe_get("homework_intime"), "homework"),
        "questions_number": plural_variant(safe_get("questions_number"), "question"),
    }


def get_student_skills(student: Student) -> list:
    """Получаем навыки студента в зависимости от программы и курса"""
    try:
        skills_data = data_cache.skills
        # courses_data = data_cache.courses

        student_program = student.statistics.get("program")
        courses_completed = student.statistics.get("courseworks_completed")

        # prof = courses_data[student_program]["profession"]
        # courses_total = courses_data[student_program]["courses_total"]

        skills = []

        skills_to_extend = skills_data.get(student_program, {}).get(courses_completed, [])

        if not skills_to_extend:
            skills.append("... Пока что нет навыков ...")
            return skills

        if "/" in skills_to_extend:
            skills.extend(skills_to_extend.split(" / "))
        else:
            skills.append(skills_to_extend)
        return skills
    except Exception as e:
        logger.error(f"Error getting skills: {e}")
        return ["Ошибка при загрузке данных из таблицы!"]


async def get_achievements_data(data: list[tuple[str, str, int]]) -> list:
    achievements_data = []
    for title, picture, receive_count in data:
        if title == "Новичок":
            continue
        achievement_logo_path = f"images/logo_{picture}"
        achievements_data.append({"title": title, "receive_count": receive_count, "image_url": achievement_logo_path})
    return achievements_data
