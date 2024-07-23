import os
from pathlib import Path
from typing import Any

from aiogram.enums import ParseMode
from aiogram.types import FSInputFile
from loguru import logger

from src.bot.client import bot
from src.config import settings
from src.dependencies import achievements, sheet_loader, stats_loader
from src.models import Achievement, Student

IMAGES_PATH = Path(__file__).parent.parent / "data" / "images"
FONT_PATH = Path(__file__).parent.parent / "static" / "fonts" / "Roboto-Bold.ttf"


def get_image_path(achievement: Achievement) -> str:
    IMAGES_PATH.mkdir(parents=True, exist_ok=True)
    return str(IMAGES_PATH / f"{achievement.type.value}.png")


def get_image_relative_path(path: str) -> str:
    path_to_image = Path(path)
    data_index = path_to_image.parts.index("images")
    relative_path = Path(*path_to_image.parts[data_index:])
    return str(relative_path)


def get_achievement_logo_relative_path(achievement: Achievement) -> str:
    path = str(IMAGES_PATH / f"logo_{achievement.picture}")
    return get_image_relative_path(path)


def get_centered_x(draw, text, font, img_width):
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    return (img_width - text_width) / 2


def generate_image(achievement: Achievement) -> str:
    """Генерируем картинку с достижением"""
    from PIL import Image, ImageDraw, ImageFont

    image_path = get_image_path(achievement)
    if os.path.exists(image_path):
        return get_image_relative_path(image_path)

    base_image = Image.open(IMAGES_PATH / "template.png")
    base_width, base_height = base_image.size

    achievement_img = Image.open(IMAGES_PATH / f"logo_{achievement.picture}").convert("RGBA")
    achievement_width, achievement_height = achievement_img.size

    achievement_x = (base_width - achievement_width) // 2
    achievement_y = 100

    base_image.paste(achievement_img, (achievement_x, achievement_y), achievement_img)

    font_title = ImageFont.truetype(FONT_PATH, 38)
    font_description = ImageFont.truetype(FONT_PATH, 20)

    draw = ImageDraw.Draw(base_image)

    title_x = get_centered_x(draw, achievement.title, font_title, base_width)
    description_x = get_centered_x(draw, achievement.description, font_description, base_width)

    draw.text((title_x, 470), achievement.title, fill="#FFFFFF", font=font_title)
    draw.text((description_x, 610), achievement.description, fill="#FFFFFF", font=font_description, align="center")

    base_image.save(image_path)
    return get_image_relative_path(image_path)


async def get_user_stats(student_id: int) -> dict[str, Any]:
    """Получаем статистику студента"""
    if str(student_id).startswith("999"):
        """ Получаем статистику из Google Sheet """
        students_data = sheet_loader.get_all_rows()
        headers = students_data[0]  # получаем заголовки из первой строки таблицы

        for row in students_data[1:]:  # начинаем с второй строки, пропуская заголовки
            if row[0] == str(student_id):
                row_values = [int(value) if value.isdigit() else value for value in row]
                return dict(zip(headers, row_values, strict=False))
        return {}  # возвращаем пустой словарь, если студент не найден

    return await stats_loader.get_stats(student_id)


def check_achievements(student: Student) -> list[Achievement]:
    """Проверка достижений"""
    achieved = []
    try:
        for a in achievements:
            if a.conditions(student.statistics):
                a.description = a.get_description(student.statistics)
                achieved.append(a)
    except Exception as e:
        logger.error(f"Ошибка при проверке достижений: {e}")
        achieved.append(achievements[0])
    return achieved


def get_student_results(student: Student) -> list:
    """Получаем результаты студента"""
    stats = student.statistics

    def safe_get(key):
        return stats.get(key) if stats.get(key) is not None else "?"

    lessons_in_program = safe_get("lessons_in_program")
    lessons_completed = safe_get("lessons_completed")

    if isinstance(lessons_in_program, int) and isinstance(lessons_completed, int):
        percent_of_lessons_completed = round((lessons_completed / lessons_in_program) * 100)
    else:
        percent_of_lessons_completed = "? "

    courseworks_in_program = safe_get("courseworks_in_program")
    courseworks_completed = safe_get("courseworks_completed")

    lives_total = safe_get("lives_total")
    lives_visited = safe_get("lives_visited")

    return [
        f"{percent_of_lessons_completed}% уроков пройдено",
        f"{lessons_completed} / {lessons_in_program} уроков пройдено",
        f"{courseworks_completed} / {courseworks_in_program} курсовых сдано",
        f"{safe_get("questions_number")} вопросов задано",
        f"{lives_visited} / {lives_total} лайвов посещено",
        f"{safe_get("lives_watched_in_record")} лайвов просмотрено в записи",
    ]


def get_student_skills(student: Student) -> list:
    """Получаем навыки студента в зависимости от программы и курса"""
    try:
        skills_data = sheet_loader.get_all_rows(worksheet_name="skills")[1:]

        if not skills_data:
            logger.error("Ошибка: нет данных по навыкам в таблице skills!")
            return ["... Нет данных по навыкам в таблице skills ..."]

        student_program = student.statistics.get("program")
        courses_completed = student.statistics.get("courseworks_completed")

        courses_data = sheet_loader.get_all_rows(worksheet_name="courses")[1:]

        if not courses_data:
            logger.error("Ошибка: нет данных по программам в таблице courses!")
            return ["... Нет данных по программам в таблице courses ..."]

        prof = [r[0] for r in courses_data if student_program == int(r[1])][0]
        courses_total = [int(r[2]) for r in courses_data if student_program == int(r[1])][0]

        skills = [f"Профессия: {prof} {student_program}, курсовых: {courses_total}"]

        for row in skills_data:
            program, courses, skills_received = int(row[1]), int(row[2]), row[3]

            if student_program and courses_completed and student_program == program and courses_completed == courses:
                if "/" in skills_received:
                    skills.extend(skills_received.split(" / "))
                else:
                    skills.append(skills_received)
                return skills
        skills.append("... Пока что нет навыков ...")
        return skills
    except Exception as e:
        logger.error(f"Ошибка при получении навыков из таблицы skills: {e}")
        return ["Ошибка при загрузке данных из таблицы!"]


async def send_telegram_updates(student_id: int, image_path: str, results: list, skills: list):
    """Отправка изображения и сообщения в телеграм-канал Skypro Sharestats"""
    image_to_channel = FSInputFile(f"data/{image_path}")
    results_text = "\n".join(f"- {result}" for result in results)
    skills_text = "\n".join(f"- {skill}" for skill in skills[1:])

    await bot.send_photo(settings.CHANNEL_ID, photo=image_to_channel)

    # Создаем сообщение с Markdown разметкой
    message_to_channel = f"*Прогресс студента {student_id}:*\n{results_text}\n\n*Уже умеет:*\n{skills_text}"
    await bot.send_message(settings.CHANNEL_ID, message_to_channel, parse_mode=ParseMode.MARKDOWN)
