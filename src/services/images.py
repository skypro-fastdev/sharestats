import re
import textwrap
from io import BytesIO
from pathlib import Path

import aiofiles
from PIL import Image, ImageDraw, ImageFont

from src.dependencies import s3_client
from src.models import Achievement

BASE_PATH = Path(__file__).parent.parent.parent
IMAGES_PATH = BASE_PATH / "data" / "images"
FONT_TITLE_PATH = BASE_PATH / "static" / "fonts" / "stratosskyeng-bold.otf"
FONT_DESCR_PATH = BASE_PATH / "static" / "fonts" / "stratosskyeng-regular.otf"


def get_images_params(orientation: str = "horizontal") -> dict:
    properties = {
        "horizontal": {
            "size": (1200, 630),
            "template": "template_1200x630.png",
            "prefix": "1200x630",
            "title_font_size": 74,
            "title_box_max_width": 680,
            "x_title": 40,
            "y_title": 205,
            "desc_font_size": 41,
            "x_desc": 42,
            "y_desc": 310,
            "desc_box_max_width": 630,
            "logo_height": 600,
            "x_logo": 650,
            "y_logo": 15,
        },
        "vertical": {
            "size": (1080, 1920),
            "template": "template_1080x1920.png",
            "prefix": "1080x1920",
            "title_font_size": 104,
            "title_box_max_width": 1000,
            "x_title": 540,
            "y_title": 1120,
            "desc_font_size": 68,
            "x_desc": 65,
            "y_desc": 1260,
            "desc_box_max_width": 950,
            "logo_height": 820,
            "x_logo": 140,
            "y_logo": 200,
        },
        "vk_post": {
            "size": (1200, 630),
            "template": "template_vk_1200x630.png",
            "prefix": "vk",
            "title_font_size": 74,
            "title_box_max_width": 680,
            "x_title": 45,
            "y_title": 130,
            "desc_font_size": 41,
            "x_desc": 47,
            "y_desc": 220,
            "desc_box_max_width": 630,
            "logo_height": 600,
            "x_logo": 650,
            "y_logo": 0,
        },
    }
    return properties[orientation]


def get_centered_x(draw, text, font, img_width):
    """Вычисляем координату по Х для центрирования текста"""
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    return (img_width - text_width) / 2


def resize_image(image, target_height):
    """Изменение размеров изображения до заданной высоты, сохраняя пропорции"""
    from PIL.Image import Resampling

    height_percent = target_height / float(image.size[1])
    target_width = int(float(image.size[0]) * float(height_percent))
    return image.resize((target_width, target_height), Resampling.LANCZOS)


def draw_wrapped_text(draw, text, font, max_width, x, y, align=None):  # noqa PLR0913
    # Получаем размеры (ширина для среднего символа 'x' и высота для символов 'hg')
    char_width = font.getbbox("x")[2] - font.getbbox("x")[0]
    char_height = font.getbbox("hg")[3] - font.getbbox("hg")[1]

    # Вычисляем, сколько символов поместится в строку
    chars_per_line = max_width // char_width

    # Разбиваем текст на строки
    lines = textwrap.wrap(text, width=chars_per_line)

    # Рисуем каждую строку
    for line in lines:
        if align == "center":
            line_bbox = draw.textbbox((0, 0), line, font=font)
            line_width = line_bbox[2] - line_bbox[0]
            line_x = x + int((max_width - line_width) / 2)
        else:
            line_x = x

        draw.text((line_x, y), line, font=font, fill="#FFFFFF")
        y += char_height + 2


def get_fitting_font(draw, text, font_path, initial_size, max_width):
    """Вычисляем шрифт, чтобы текст поместился в заданный прямоугольник в title"""
    font_size = initial_size
    font = ImageFont.truetype(font_path, font_size)
    while font_size > 50:
        text_width = draw.textlength(text, font=font)
        if text_width <= max_width:
            break
        font_size -= 1
        font = ImageFont.truetype(font_path, font_size)
    return font


def get_image_relative_path(path: str) -> str:
    """Получаем относительный путь к изображению в формате /images/..."""
    path_to_image = Path(path)
    data_index = path_to_image.parts.index("images")
    relative_path = Path(*path_to_image.parts[data_index:])
    return str(relative_path)


def get_achievement_logo_relative_path(achievement: Achievement) -> str:
    return str(Path("images") / f"logo_{achievement.picture}")


def remove_tags(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text)


async def find_or_generate_image(achievement: Achievement, orientation: str) -> dict | None:
    """Ищем или генерируем изображение для данного достижения"""
    params = get_images_params(orientation)
    prefix = params["prefix"]

    image_name = f"{prefix}/{achievement.profession}/{achievement.type.value}.png"

    try:
        # Проверяем, существует ли файл в S3
        if await s3_client.check_file_exists(image_name):
            return {
                "url": s3_client.get_public_url(image_name),
                "width": params["size"][0],
                "height": params["size"][1],
            }

        async with aiofiles.open(IMAGES_PATH / params["template"], mode="rb") as f:
            base_image_data = await f.read()
            base_image = Image.open(BytesIO(base_image_data))

        async with aiofiles.open(IMAGES_PATH / f"logo_{achievement.picture}", mode="rb") as f:
            achievement_img_data = await f.read()
            achievement_img = Image.open(BytesIO(achievement_img_data)).convert("RGBA")
    except Exception:
        return None

    achievement_img = resize_image(achievement_img, params["logo_height"])
    achievement_x, achievement_y = params["x_logo"], params["y_logo"]

    # Вставляем лого achievement на изображении
    base_image.paste(achievement_img, (achievement_x, achievement_y), achievement_img)

    font_description = ImageFont.truetype(FONT_DESCR_PATH, params["desc_font_size"])

    draw = ImageDraw.Draw(base_image)

    width, height = params["size"]

    # Рассчитываем размеры для шрифта title чтобы влезал на картинку
    font_title = get_fitting_font(
        draw, achievement.title, FONT_TITLE_PATH, params["title_font_size"], params["title_box_max_width"]
    )

    if params["size"] == (1080, 1920):
        params["x_title"] = get_centered_x(draw, achievement.title, font_title, width)

    # Рисуем title на изображении
    draw.text(
        (params["x_title"], params["y_title"]), achievement.title, fill="#FFFFFF", font=font_title, align="center"
    )

    align_text = "center" if params["size"] == (1080, 1920) else "left"

    # Рисуем description на изображении
    draw_wrapped_text(
        draw,
        remove_tags(achievement.description),
        font_description,
        params["desc_box_max_width"],
        params["x_desc"],
        params["y_desc"],
        align=align_text,
    )

    try:
        # Сохраняем изображение в байтовый объект
        with BytesIO() as img_byte_arr:
            base_image.save(img_byte_arr, format="PNG", optimize=False, compress_level=0)
            image_bytes = img_byte_arr.getvalue()

            # Загружаем изображение в S3
            url = await s3_client.upload_file(image_bytes, image_name)

        return {"url": url, "width": width, "height": height}
    except Exception:
        return None
