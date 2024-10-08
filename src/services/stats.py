from asyncio.exceptions import TimeoutError
from typing import Any, Sequence

from loguru import logger
from sqlalchemy import Row

from src.bot.logger import tg_logger
from src.dependencies import achievements, data_cache, stats_loader
from src.models import Achievement, Student


async def get_user_stats(student_id: int) -> dict[str, Any]:
    """Получаем статистику студента"""
    try:
        if str(student_id).startswith("999"):  # моковые данные для тестов
            return data_cache.stats.get(student_id, {})
        stats = await stats_loader.get_stats(student_id)
        return {k: v for k, v in stats.items() if v is not None}
    except TimeoutError:
        await tg_logger.log("ERROR", f"Timeout error while getting stats for student_id {student_id}")
        return {}


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


def plural_variant(n: int | str, type_: str) -> str:
    """Форматирование множественного числа"""
    if n == "?":
        return n

    match type_:
        case "homework":
            text = ["домашка", "домашки", "домашек"]
        case "question":
            text = ["вопрос", "вопроса", "вопросов"]
        case "rate":
            text = ["оценка", "оценки", "оценок"]
        case "live":
            text = ["лайв", "лайва", "лайвов"]
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
        "lives_visited": plural_variant(safe_get("lives_visited"), "live"),
        "lives_watched_in_record": plural_variant(safe_get("lives_watched_in_record"), "live"),
        "homework_morning": plural_variant(safe_get("homework_morning"), "homework"),
        "homework_night": plural_variant(safe_get("homework_night"), "homework"),
        "homework_weekend": plural_variant(safe_get("homework_weekend"), "homework"),
        "homework_last_6": plural_variant(safe_get("homework_last_6"), "homework"),
        "questions_number": plural_variant(safe_get("questions_number"), "question"),
        "rates_created": plural_variant(safe_get("rates_created"), "rate"),
    }


def get_student_skills(student: Student) -> list:
    """Получаем навыки студента в зависимости от программы и курса"""
    try:
        skills_data = data_cache.skills_details

        student_program = student.statistics.get("program")
        student_lessons_completed = student.statistics.get("lessons_completed")

        skills = []
        program_skills = skills_data.get(student_program, {})

        for lessons_to_complete in program_skills:
            if student_lessons_completed >= lessons_to_complete:
                skills.append(program_skills[lessons_to_complete])
            else:
                break

        return skills
    except Exception as e:
        logger.error(f"Error getting skills: {e}")
        return []


async def get_achievements_data(data: Sequence[Row]) -> list:
    achievements_data = []
    for title, picture, receive_count in data:
        if title == "Новичок":
            continue
        achievement_logo_path = f"images/logo_{picture}"
        achievements_data.append({"title": title, "receive_count": receive_count, "image_url": achievement_logo_path})
    return achievements_data


def get_meme_stats(meme_stats: dict) -> dict:
    if meme_stats:
        answer_to_question = {meme.id: meme.question for meme in data_cache.meme_data.values()}

        for key, answer in meme_stats.items():
            if answer_to_question.get(key) is not None:
                meme_stats[key] = {"question": answer_to_question[key], "answer": answer}
    return meme_stats
