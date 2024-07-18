from random import choice

from fastapi import APIRouter, Form, status
from fastapi.requests import Request
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates

from src.models import Student
from src.utils import (
    check_achievements,
    generate_image,
    get_achievement_logo_relative_path,
    get_student_results,
    get_student_skills,
    get_user_stats,
)

router = APIRouter()

templates = Jinja2Templates(directory="src/templates")


@router.get("/")
async def index():
    return JSONResponse(status_code=status.HTTP_200_OK, content={"status": "ok"})


@router.get("/generate/{student_id}")
async def generate(request: Request, student_id: int):
    stats = get_user_stats(student_id)  # берём данные из Google Sheet

    if not stats:
        return PlainTextResponse(f"Студент с id {student_id} не найден", 404)

    student = Student(id=student_id, statistics=stats)

    achievements = check_achievements(student)
    # Выбираем случайное достижение если их несколько, иначе достижение первое "newby"
    achievement = choice(achievements[1:]) if len(achievements) > 1 else achievements[0]  # noqa: S311

    path_to_image = generate_image(achievement)
    results = get_student_results(student)
    skills = get_student_skills(student)

    return templates.TemplateResponse(
        "stats.html",
        {
            "request": request,
            "student_id": student.id,
            "results": results,
            "skills": skills,
            "achievement_image": path_to_image,
        },
    )


@router.get("/share/{student_id}")
async def share(request: Request, student_id: int):
    stats = get_user_stats(student_id)  # берём данные из Google Sheet

    if not stats:
        return PlainTextResponse(f"Студент с id {student_id} не найден", 404)

    student = Student(id=student_id, first_name="Маша", last_name="Миллер", statistics=stats)

    achievements = check_achievements(student)
    # Выбираем случайное достижение если их несколько, иначе достижение первое "newby"
    achievement = choice(achievements[1:]) if len(achievements) > 1 else achievements[0]  # noqa: S311

    achievement_image = get_achievement_logo_relative_path(achievement)

    return templates.TemplateResponse(
        "share.html",
        {
            "request": request,
            "logo_image": "images/skypro.png",
            "achievement_image": achievement_image,
            "first_name": student.first_name,
            "full_name": f"{student.first_name} {student.last_name}",
            "title": achievement.title,
            "description": achievement.description,
        },
    )


@router.post("/sent")
async def form_sent(request: Request, phone: str = Form(...)):
    return templates.TemplateResponse("sent.html", {"request": request, "phone": phone})
