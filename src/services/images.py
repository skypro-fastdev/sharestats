import re
import textwrap
from io import BytesIO
from pathlib import Path

import aiofiles
import aiohttp
from fastapi import HTTPException
from loguru import logger
from PIL import Image, ImageDraw, ImageFont

from src.dependencies import s3_client
from src.models import Achievement, Badge

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
        "vk_badge": {
            "size": (1200, 630),
            "template": "template_badge_1200x630.png",
            "prefix": "vk",
            "title_font_size": 70,
            "title_box_max_width": 640,
            "x_title": 45,
            "y_title": 160,
            "desc_font_size": 41,
            "x_desc": 47,
            "y_desc": 340,
            "desc_box_max_width": 630,
            "logo_height": 380,
            "x_logo": 660,
            "y_logo": 115,
        },
        "tg_badge": {
            "size": (1080, 1920),
            "template": "template_badge_1080x1920.png",
            "prefix": "tg",
            "title_font_size": 104,
            "title_box_max_width": 950,
            "x_title": 65,
            "y_title": 330,
            "desc_font_size": 68,
            "x_desc": 65,
            "y_desc": 1320,
            "desc_box_max_width": 950,
            "logo_height": 500,
            "x_logo": 190,
            "y_logo": 700,
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


async def check_s3_file_exists(image_name: str, params: dict) -> dict | None:
    if await s3_client.check_file_exists(image_name):
        return {
            "url": s3_client.get_public_url(image_name),
            "width": params["size"][0],
            "height": params["size"][1],
        }
    return None


async def open_image(path: str | Path, rgba: bool = False) -> Image.Image:
    async with aiofiles.open(path, mode="rb") as f:
        image_data = await f.read()
        if rgba:
            return Image.open(BytesIO(image_data)).convert("RGBA")
        return Image.open(BytesIO(image_data))


async def upload_to_s3(image: Image.Image, image_name: str) -> str:
    """Возращает ссылку на изображение в S3"""
    with BytesIO() as img_byte_arr:
        image.save(img_byte_arr, format="PNG", optimize=False, compress_level=0)
        image_bytes = img_byte_arr.getvalue()
        return await s3_client.upload_file(image_bytes, image_name)  # Загружаем изображение в S3


async def find_or_generate_image(obj: Achievement | Badge, orientation: str) -> dict | None:
    """Ищем или генерируем изображение для данного достижения"""
    params = get_images_params(orientation)
    prefix = params["prefix"]

    if isinstance(obj, Achievement):
        image_name = f"{prefix}/{obj.profession}/{obj.type.value}.png"
    else:
        image_name = f"badges/{prefix}/{obj.badge_type}.png"

    try:
        # Проверяем, существует ли файл в S3
        image_exist = await check_s3_file_exists(image_name, params)
        if image_exist:
            return image_exist

        # Если нет, то генерируем его
        base_image = await open_image(IMAGES_PATH / params["template"])
        if isinstance(obj, Achievement):
            logo_img = await open_image(IMAGES_PATH / f"logo_{obj.picture}", rgba=True)
        else:
            logo_img = await open_image(IMAGES_PATH / "badges" / f"{obj.badge_type}.png", rgba=True)

    except Exception:
        return None

    logo_resized = resize_image(logo_img, params["logo_height"])
    achievement_x, achievement_y = params["x_logo"], params["y_logo"]

    # Вставляем лого на изображении
    base_image.paste(logo_resized, (achievement_x, achievement_y), logo_resized)

    font_description = ImageFont.truetype(FONT_DESCR_PATH, params["desc_font_size"])

    draw = ImageDraw.Draw(base_image)

    width, height = params["size"]

    # Рассчитываем размеры для шрифта title чтобы влезал на картинку
    if isinstance(obj, Achievement):
        font_title = get_fitting_font(
            draw, obj.title, FONT_TITLE_PATH, params["title_font_size"], params["title_box_max_width"]
        )
    else:
        font_title = ImageFont.truetype(FONT_TITLE_PATH, params["title_font_size"])

    if params["size"] == (1080, 1920) and isinstance(obj, Achievement):
        params["x_title"] = get_centered_x(draw, obj.title, font_title, width)

    # Рисуем title на изображении
    if isinstance(obj, Achievement):
        draw.text((params["x_title"], params["y_title"]), obj.title, fill="#FFFFFF", font=font_title, align="center")
    else:
        draw_wrapped_text(
            draw,
            obj.title,
            font_title,
            params["title_box_max_width"],
            params["x_title"],
            params["y_title"],
            align="center" if params["size"] == (1080, 1920) else "left",
        )

    align_text = "center" if params["size"] == (1080, 1920) else "left"

    # Рисуем description на изображении
    draw_wrapped_text(
        draw,
        remove_tags(obj.description),
        font_description,
        params["desc_box_max_width"],
        params["x_desc"],
        params["y_desc"],
        align=align_text,
    )

    try:
        # if isinstance(obj, Badge):
        #     async with aiofiles.open(IMAGES_PATH / "badges" / f"saved_{obj.badge_type}.png", mode="wb") as f:
        #         with BytesIO() as img_byte_arr:
        #             base_image.save(img_byte_arr, format="PNG", optimize=False, compress_level=9)
        #             image_bytes = img_byte_arr.getvalue()
        #             await f.write(image_bytes)
        #     return {"url": f"badges/saved_{obj.badge_type}.png", "width": width, "height": height}

        url = await upload_to_s3(base_image, image_name)
        return {"url": url, "width": width, "height": height}
    except Exception:
        return None


async def get_image_data(achievement: Achievement, orientation: str) -> dict:
    image_data = await find_or_generate_image(achievement, orientation)
    if not image_data:
        logger.error(f"Failed to get image for achievement: {achievement.title}")
        raise HTTPException(status_code=500, detail="Failed to get image")
    return image_data


async def fetch_image(image_url: str) -> tuple:
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(image_url) as response:
                if response.status != 200:
                    raise HTTPException(status_code=500, detail="Failed to fetch image")

                image_bytes = await response.read()
                content_type = response.headers.get("Content-Type", "image/png")
                filename = image_url.split("/")[-1]

                return image_bytes, content_type, filename
        except Exception as e:
            logger.error(f"Failed to fetch image: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to fetch image") from e
