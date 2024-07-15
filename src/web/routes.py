from random import choice

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from starlette.background import BackgroundTask

from src.models import Student
from src.utils import check_achievements, close_file, generate_image, get_user_stats

router = APIRouter()

templates = Jinja2Templates(directory="src/templates")


@router.get("/")
async def index():
    return JSONResponse(status_code=status.HTTP_200_OK, content={"status": "ok"})


@router.get("/generate/{student_id}")
async def generate(student_id: int):
    stats = get_user_stats(student_id)  # берём данные из Google Sheet

    if not stats:
        raise HTTPException(status_code=404, detail=f"Student with id {student_id} not found")

    student = Student(id=student_id, statistics=stats)

    achievements = check_achievements(student)

    # Выбираем случайное достижение если их несколько, иначе достижение первое "newby"
    achievement = choice(achievements[1:]) if len(achievements) > 1 else achievements[0]  # noqa: S311

    path_to_image = generate_image(achievement)

    image = open(path_to_image, "rb")  # noqa: ASYNC230, SIM115
    return StreamingResponse(image, media_type="image/png", background=BackgroundTask(close_file, image))
