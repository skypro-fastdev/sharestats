from fastapi import APIRouter, Depends, status
from fastapi.requests import Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src.classes.simple_storage import SimpleStorage
from src.config import settings
from src.utils import (
    find_or_generate_image,
    get_achievement_logo_relative_path,
    get_stats,
    get_student_skills,
    send_telegram_updates,
)
from src.web.handlers import StudentHandler, get_student_handler


def get_simple_storage() -> SimpleStorage:
    return SimpleStorage()


router = APIRouter()

templates = Jinja2Templates(directory="src/templates")


def is_social_bot(request):
    user_agent = request.headers.get("User-Agent", "").lower()
    referer = request.headers.get("Referer", "")

    bots = ("telegrambot", "instagram", "facebookexternalhit", "linkedinbot", "vkshare")  # 'twitterbot'
    social_referers = ("instagram.com", "facebook.com", "t.co", "t.me", "linkedin.com")  # 'twitter.com', 'vk.com'

    is_bot = any(bot in user_agent for bot in bots)
    is_social_referer = any(social in referer for social in social_referers)
    is_facebook_preview = request.headers.get("X-Purpose") == "preview"

    return is_bot or is_social_referer or is_facebook_preview


@router.get("/")
async def index():
    return JSONResponse(status_code=status.HTTP_200_OK, content={"status": "ok"})


@router.get("/stats/{student_id}", name="stats")
async def stats(
    request: Request,
    student_id: int,
    handler: StudentHandler = Depends(get_student_handler),
    storage: SimpleStorage = Depends(get_simple_storage),
):
    achievement_logo = get_achievement_logo_relative_path(handler.achievement)

    student_stats = get_stats(handler.student)
    skills = get_student_skills(handler.student)

    storage.set(student_id, handler.achievement, handler)

    context = {
        "request": request,
        "student_id": handler.student.id,
        "days_since_start": handler.student.days_since_start,
        "profession": handler.student.profession.value,
        "skills": skills[1:],  # отсекаем первый элемент, т.к. он для тестов!
        "title": handler.achievement.title,
        "description": handler.achievement.description,
        "achievement_logo": achievement_logo,
        "tg_link": settings.TG_CHANNEL,
    }
    context.update(student_stats)

    return templates.TemplateResponse("stats.html", context)


@router.get("/get_image/{student_id}", name="get_image")
async def get_image(
    request: Request, student_id: int, share_to: str, storage: SimpleStorage = Depends(get_simple_storage)
):
    data = storage.get(student_id)
    achievement = data.get("achievement")
    image_path = await find_or_generate_image(achievement, platform=share_to)
    full_image_url = str(request.url_for("data", path=image_path))

    return RedirectResponse(full_image_url, status_code=status.HTTP_302_FOUND)


@router.get("/share/{student_id}", name="share")
async def share(request: Request, share_to: str, handler: StudentHandler = Depends(get_student_handler)):
    if not share_to:
        image_data = await handler.gen_image(platform="vk_post")
    else:
        image_data = await handler.gen_image(platform=share_to)

    if is_social_bot(request):
        return templates.TemplateResponse(
            "share.html",
            {
                "request": request,
                "student_id": handler.student_id,
                "title": handler.achievement.title,
                "description": handler.achievement.description,
                "achievement_image": image_data["path"],
                "image_width": image_data["width"],
                "image_height": image_data["height"],
            },
        )

    return RedirectResponse(
        request.url_for("referal", student_id=handler.student_id), status_code=status.HTTP_302_FOUND
    )


@router.get("/tg/{student_id}", name="tg")
async def tg(request: Request, student_id: int, storage: SimpleStorage = Depends(get_simple_storage)):
    data = storage.get(student_id)
    achievement = data.get("achievement")
    image_path = await find_or_generate_image(achievement, platform="telegram")

    referal_url = str(request.url_for("referal", student_id=student_id))
    #
    # storage.pop(student_id)  # remove student data from storage

    await send_telegram_updates(referal_url, image_path)

    response = RedirectResponse(settings.TG_CHANNEL, status_code=status.HTTP_302_FOUND)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@router.get("/s/{student_id}", name="referal")
async def referal(request: Request, student_id: int, storage: SimpleStorage = Depends(get_simple_storage)):
    data = storage.get(student_id)
    achievement = data.get("achievement")
    handler = data.get("handler")

    achievement_logo = get_achievement_logo_relative_path(achievement)

    student_stats = get_stats(handler.student)
    skills = get_student_skills(handler.student)

    context = {
        "request": request,
        "student_id": handler.student.id,
        "days_since_start": handler.student.days_since_start,
        "profession": handler.student.profession.value,
        "profession_dative": handler.student.profession.dative,
        "skills": skills[1:],  # отсекаем первый элемент, т.к. он для тестов!
        "title": handler.achievement.title,
        "description": handler.achievement.description,
        "achievement_logo": achievement_logo,
    }
    context.update(student_stats)

    return templates.TemplateResponse("referal.html", context)
