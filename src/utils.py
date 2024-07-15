import os
from pathlib import Path
from typing import Any

from loguru import logger

from src.dependencies import achievements, sheet_loader
from src.models import Achievement, Student

IMAGES_PATH = Path(__file__).parent.parent / "data" / "images"
FONT_PATH = Path(__file__).parent.parent / "static" / "fonts" / "Roboto-Bold.ttf"


def get_image_path(achievement: Achievement) -> str:
    IMAGES_PATH.mkdir(parents=True, exist_ok=True)
    return str(IMAGES_PATH / f"{achievement.type.value}.png")


def get_centered_x(draw, text, font, img_width):
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    return (img_width - text_width) / 2


def generate_image(achievement: Achievement) -> Path:
    """Генерируем картинку с достижением"""
    from PIL import Image, ImageDraw, ImageFont

    image_path = get_image_path(achievement)
    if os.path.exists(image_path):
        return Path(image_path)

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
    return Path(image_path)


def get_user_stats(student_id: int) -> dict[str, Any]:
    """Получаем статистику временно из Google Sheet"""
    data = sheet_loader.get_all_rows()
    headers = data[0]  # получаем заголовки из первой строки таблицы

    for row in data[1:]:  # начинаем с второй строки, пропуская заголовки
        if row[0] == str(student_id):
            row_values = [int(value) if value.isdigit() else value for value in row]
            return dict(zip(headers, row_values, strict=False))
    return {}  # возвращаем пустой словарь, если студент не найден


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


def close_file(file):
    file.close()
