from random import choice

from fastapi import APIRouter, status
from fastapi.requests import Request
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates

from src.models import Student
from src.utils import check_achievements, generate_image, get_student_results, get_student_skills, get_user_stats

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
