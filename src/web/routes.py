from fastapi import APIRouter, Depends, Form, status
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates

from src.utils import (
    get_achievement_logo_relative_path,
    get_student_results,
    get_student_skills,
    send_telegram_updates,
)
from src.web.handlers import StudentHandler, get_student_handler

router = APIRouter()

templates = Jinja2Templates(directory="src/templates")


@router.get("/")
async def index():
    return JSONResponse(status_code=status.HTTP_200_OK, content={"status": "ok"})


@router.get("/opengraph/{student_id}")
async def opengraph_image(request: Request, handler: StudentHandler = Depends(get_student_handler)):
    path_to_image = handler.gen_image()

    return templates.TemplateResponse(
        "opengraph.html",
        {
            "request": request,
            "student_id": handler.student_id,
            "title": handler.achievement.title,
            "description": handler.achievement.description,
            "achievement_image": path_to_image,
        },
    )


@router.get("/generate/{student_id}")
async def generate(request: Request, handler: StudentHandler = Depends(get_student_handler)):
    path_to_image = handler.gen_image()
    results = get_student_results(handler.student)
    skills = get_student_skills(handler.student)

    # Отправка изображения и сообщения в телеграм-канал
    await send_telegram_updates(handler.student_id, path_to_image, results, skills)

    return templates.TemplateResponse(
        "stats.html",
        {
            "request": request,
            "student_id": handler.student.id,
            "results": results,
            "skills": skills,
            "achievement_image": path_to_image,
        },
    )


@router.get("/share/{student_id}")
async def share(request: Request, handler: StudentHandler = Depends(get_student_handler)):
    achievement_image = get_achievement_logo_relative_path(handler.achievement)

    return templates.TemplateResponse(
        "share.html",
        {
            "request": request,
            "logo_image": "images/skypro.png",
            "achievement_image": achievement_image,
            "first_name": handler.student.first_name,
            "full_name": f"{handler.student.first_name} {handler.student.last_name}",
            "title": handler.achievement.title,
            "description": handler.achievement.description,
        },
    )


@router.post("/sent")
async def form_sent(request: Request, phone: str = Form(...)):
    return templates.TemplateResponse("sent.html", {"request": request, "phone": phone})
