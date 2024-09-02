from datetime import datetime

from fastapi import HTTPException
from loguru import logger

from src.db.models import AchievementDB, StudentDB
from src.db.students_crud import StudentDBHandler
from src.models import Achievement, Student
from src.web.handlers import StudentHandler


class NoDataException(Exception):  # noqa N818
    pass


async def get_student_data(handler: StudentHandler, student_id: int) -> Student:
    if not handler.student:
        logger.info(f"Statistics for student {student_id} not found")
        raise HTTPException(status_code=404, detail="Страница не найдена")

    if not handler.achievement:
        logger.info(f"Student {student_id} has no achievement")
        raise HTTPException(status_code=404, detail="Страница не найдена")

    homework_total = handler.student.statistics.get("homework_total")
    started_at = handler.student.started_at
    today = datetime.today().date()

    if homework_total == 0 or started_at > today:
        raise NoDataException()

    return handler.student


async def get_student_by_id(crud: StudentDBHandler, student_id: int) -> Student:
    db_student = await crud.get_student(student_id)
    if not db_student:
        logger.error(f"Student {student_id} not found in DB")
        raise HTTPException(status_code=404, detail="Страница не найдена")
    return db_student.to_student()


async def update_or_create_student_in_db(crud: StudentDBHandler, student: Student) -> StudentDB:
    db_student = await crud.get_student(student.id)

    if db_student:
        db_student = await crud.update_student(student)
    else:
        db_student = await crud.create_student(student)

    if not db_student:
        raise HTTPException(status_code=500, detail="Failed to create/update student in DB")

    return db_student


async def update_or_create_achievement_in_db(crud: StudentDBHandler, achievement: Achievement) -> AchievementDB:
    db_achievement = await crud.get_achievement_by_title_and_profession(achievement.title, achievement.profession)
    if not db_achievement:
        db_achievement = await crud.create_achievement(achievement)

    if not db_achievement:
        raise HTTPException(status_code=500, detail="Failed to create achievement")

    return db_achievement


async def get_achievement_for_student(crud: StudentDBHandler, student_id: int) -> Achievement:
    db_achievement = await crud.get_achievement_by_student_id(student_id)
    if not db_achievement:
        raise HTTPException(status_code=404, detail="Страница не найдена")
    return db_achievement.to_achievement_model()


async def add_meme_stats_to_student(crud: StudentDBHandler, student_id: int, memes: list) -> None:
    db_student = await crud.add_memes_stats_to_student(student_id, memes)
    if not db_student:
        logger.error(f"Student {student_id} not found in DB while adding meme stats")
        raise HTTPException(status_code=500, detail="Failed to add meme stats to student")
