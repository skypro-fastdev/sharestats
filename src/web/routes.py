from fastapi import APIRouter, Depends, Form, status
from fastapi.requests import Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src.classes.simple_storage import SimpleStorage
from src.utils import (
    find_or_generate_image,
    get_achievement_logo_relative_path,
    get_stats,
    get_student_results,
    get_student_skills,
    send_telegram_updates,
    send_test_telegram_updates,
)
from src.web.handlers import StudentHandler, get_student_handler

TG_CHANNGEL = "https://t.me/skypro_sharingstats"


def get_simple_storage() -> SimpleStorage:
    return SimpleStorage()


router = APIRouter()

templates = Jinja2Templates(directory="src/templates")


@router.get("/")
async def index():
    return JSONResponse(status_code=status.HTTP_200_OK, content={"status": "ok"})


@router.get("/opengraph/{student_id}", name="opengraph")
async def opengraph_image(request: Request, share_to: str, handler: StudentHandler = Depends(get_student_handler)):
    if not share_to:
        image_data = await handler.gen_image(platform="vk_post")
    else:
        image_data = await handler.gen_image(platform=share_to)

    return templates.TemplateResponse(
        "opengraph.html",
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


@router.get("/generate/{student_id}", name="generate")
async def generate(request: Request, handler: StudentHandler = Depends(get_student_handler)):
    image_data = await handler.gen_image(platform="vk_stories")
    path_to_image = image_data["path"]
    results = get_student_results(handler.student)
    skills = get_student_skills(handler.student)

    # Отправка изображения и сообщений с результатами в телеграм-канал
    await send_test_telegram_updates(handler.student_id, path_to_image, results, skills)

    return templates.TemplateResponse(
        "stats.html",
        {
            "request": request,
            "student_id": handler.student.id,
            "results": results,
            "skills": skills,
            "achievement_image": path_to_image,
            "image_width": image_data["width"],
            "image_height": image_data["height"],
        },
    )


#
# @router.get("/share/{student_id}", name="share")
# async def share(request: Request, handler: StudentHandler = Depends(get_student_handler)):
#     achievement_image = get_achievement_logo_relative_path(handler.achievement)
#
#     return templates.TemplateResponse(
#         "old_share.html",
#         {
#             "request": request,
#             "logo_image": "images/skypro.png",
#             "achievement_image": achievement_image,
#             "first_name": handler.student.first_name,
#             "full_name": f"{handler.student.first_name} {handler.student.last_name}",
#             "title": handler.achievement.title,
#             "description": handler.achievement.description,
#         },
#     )


@router.post("/sent")
async def form_sent(request: Request, phone: str = Form(...)):
    return templates.TemplateResponse("sent.html", {"request": request, "phone": phone})


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
        "tg_link": TG_CHANNGEL,
    }
    context.update(student_stats)

    return templates.TemplateResponse("student_stats.html", context)


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


@router.get("/tg/{student_id}", name="tg")
async def tg(request: Request, student_id: int, storage: SimpleStorage = Depends(get_simple_storage)):
    data = storage.get(student_id)
    achievement = data.get("achievement")
    image_path = await find_or_generate_image(achievement, platform="telegram")

    full_image_url = str(request.url_for("data", path=image_path))
    #
    # storage.pop(student_id)  # remove student data from storage

    await send_telegram_updates(full_image_url, image_path)

    response = RedirectResponse(TG_CHANNGEL, status_code=status.HTTP_302_FOUND)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response
