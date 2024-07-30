from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.requests import Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src.config import IS_HEROKU, settings
from src.db.crud import StudentCRUD, get_student_crud
from src.utils import (
    async_generate_image,
    find_or_generate_image,
    get_achievement_logo_relative_path,
    get_stats,
    get_student_skills,
    send_telegram_updates,
)
from src.web.handlers import StudentHandler, get_student_handler

router = APIRouter()

templates = Jinja2Templates(directory="src/templates")

HOST_URL = "https://sky.pro/share" if IS_HEROKU else "http://127.0.0.1:8000/share"


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
    crud: StudentCRUD = Depends(get_student_crud),
):
    achievement_logo = get_achievement_logo_relative_path(handler.achievement)

    student_stats = get_stats(handler.student)
    skills = get_student_skills(handler.student)

    db_student = await crud.get_student(student_id)

    if not db_student:
        db_student = await crud.create_update_student(handler.student)
    if not db_student:
        raise HTTPException(status_code=500, detail="Failed to create or update student")

    # Получаем или создаем достижение
    db_achievement = await crud.get_achievement_by_title_and_profession(
        handler.achievement.title, handler.achievement.profession
    )
    if not db_achievement:
        db_achievement = await crud.create_achievement(handler.achievement)
        await crud.add_achievement_to_student(db_student.id, db_achievement.id)
    if not db_achievement:
        raise HTTPException(status_code=500, detail="Failed to create achievement")

    context = {
        "request": request,
        "student_id": handler.student.id,
        "days_since_start": handler.student.days_since_start,
        "profession": handler.student.profession.value,
        "skills": skills,
        "title": handler.achievement.title,
        "description": handler.achievement.description,
        "achievement_logo": achievement_logo,
        "tg_link": settings.TG_CHANNEL,
        "base_url": HOST_URL,
    }
    context.update(student_stats)

    return templates.TemplateResponse("stats.html", context)


@router.get("/get_image/{student_id}", name="get_image")
async def get_image(
    request: Request,
    student_id: int,
    crud: StudentCRUD = Depends(get_student_crud),
):
    db_achievement = await crud.get_achievement_by_student_id(student_id)

    if not db_achievement:
        raise HTTPException(status_code=404, detail=f"Достижение для студента с id {student_id} не найдено")

    achievement = db_achievement.to_achievement_model()
    image_path = await find_or_generate_image(achievement, "vertical")
    full_image_url = str(request.url_for("data", path=image_path))

    return RedirectResponse(full_image_url, status_code=status.HTTP_302_FOUND)


@router.get("/h/{student_id}", name="share_horizontal")
@router.get("/v/{student_id}", name="share_vertical")
async def share(
    request: Request,
    student_id: int,
    # handler: StudentHandler = Depends(get_student_handler),
    crud: StudentCRUD = Depends(get_student_crud),
):
    orientation = "horizontal" if "/h/" in request.url.path else "vertical"

    db_achievement = await crud.get_achievement_by_student_id(student_id)

    if not db_achievement:
        raise HTTPException(status_code=404, detail=f"Достижение для студента с id {student_id} не найдено")

    achievement = db_achievement.to_achievement_model()

    image_data = await async_generate_image(achievement, orientation)

    if is_social_bot(request):
        return templates.TemplateResponse(
            "share.html",
            {
                "request": request,
                "student_id": student_id,
                "title": achievement.title,
                "description": achievement.description,
                "achievement_image": image_data["path"],
                "image_width": image_data["width"],
                "image_height": image_data["height"],
                "base_url": HOST_URL,
            },
        )

    return RedirectResponse(request.url_for("referal", student_id=student_id), status_code=status.HTTP_302_FOUND)


@router.get("/tg/{student_id}", name="tg")
async def tg(
    request: Request,
    student_id: int,
    crud: StudentCRUD = Depends(get_student_crud),
):
    db_achievement = await crud.get_achievement_by_student_id(student_id)

    if not db_achievement:
        raise HTTPException(status_code=404, detail=f"Достижение для студента с id {student_id} не найдено")

    achievement = db_achievement.to_achievement_model()
    image_path = await find_or_generate_image(achievement, "vertical")

    referal_url = str(request.url_for("referal", student_id=student_id))

    await send_telegram_updates(referal_url, image_path)

    response = RedirectResponse(settings.TG_CHANNEL, status_code=status.HTTP_302_FOUND)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@router.get("/s/{student_id}", name="referal")
async def referal(
    request: Request,
    student_id: int,
    crud: StudentCRUD = Depends(get_student_crud),
):
    db_achievement = await crud.get_achievement_by_student_id(student_id)

    if not db_achievement:
        raise HTTPException(status_code=404, detail=f"Достижение для студента с id {student_id} не найдено")

    achievement = db_achievement.to_achievement_model()

    db_student = await crud.get_student(student_id)

    if not db_student:
        raise HTTPException(status_code=404, detail=f"Студент с id {student_id} не найден")

    student = db_student.to_student()

    achievement_logo = get_achievement_logo_relative_path(achievement)

    student_stats = get_stats(student)
    skills = get_student_skills(student)

    context = {
        "request": request,
        "student_id": student.id,
        "days_since_start": student.days_since_start,
        "profession": student.profession.value,
        "profession_dative": student.profession.dative,
        "skills": skills,
        "title": achievement.title,
        "description": achievement.description,
        "achievement_logo": achievement_logo,
    }
    context.update(student_stats)

    return templates.TemplateResponse("referal.html", context)
