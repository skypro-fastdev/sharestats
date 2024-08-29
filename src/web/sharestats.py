import aiohttp
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.requests import Request
from fastapi.responses import JSONResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from loguru import logger

from src.config import IS_HEROKU, settings
from src.db.students_crud import StudentDBHandler, get_student_crud
from src.dependencies import sheet_pusher
from src.models import PhoneSubmission, ProfessionEnum, URLSubmission
from src.services.images import fetch_image, get_achievement_logo_relative_path, get_image_data
from src.services.security import verify_hash
from src.services.stats import get_achievements_data, get_stats, get_student_skills
from src.services.student_service import (
    NoDataException,
    get_achievement_for_student,
    get_student_by_id,
    get_student_data,
    update_or_create_achievement_in_db,
    update_or_create_student_in_db,
)
from src.services.telegram import send_telegram_updates
from src.web.handlers import StudentHandler, get_student_handler
from src.web.utils import add_no_cache_headers, get_orientation, is_social_bot

router = APIRouter()

templates = Jinja2Templates(directory="src/templates")

HOST_URL = "https://sky.pro/share" if IS_HEROKU else "http://127.0.0.1:8000/share"
STUDENT_DASHBOARD = "https://my.sky.pro/student-cabinet/"


@router.get("/stats/{student_id}", name="stats")
async def stats(
    request: Request,
    student_id: int,
    hash: str | None = None,  # noqa: A002
    handler: StudentHandler = Depends(get_student_handler),
    crud: StudentDBHandler = Depends(get_student_crud),
):
    if not verify_hash(student_id, hash):
        if handler.student and handler.student.profession == ProfessionEnum.GD:
            pass
        else:
            raise HTTPException(status_code=404, detail="Страница не найдена")

    try:
        student = await get_student_data(handler, student_id)
        db_student = await update_or_create_student_in_db(crud, student)
        db_achievement = await update_or_create_achievement_in_db(crud, handler.achievement)
        await crud.add_achievement_to_student(db_student.id, db_achievement.id)

        context = {
            "request": request,
            "student_id": student.id,
            "student_name": f"{student.first_name} {student.last_name}",
            "days_since_start": student.days_since_start,
            "profession": student.profession.value,
            "skills": get_student_skills(student),
            "title": handler.achievement.title,
            "description": handler.achievement.description,
            "achievement_logo": get_achievement_logo_relative_path(handler.achievement),
            "tg_link": settings.TG_CHANNEL,
            "base_url": HOST_URL,
            **get_stats(student),
        }

        return add_no_cache_headers(templates.TemplateResponse("stats.html", context))

    except NoDataException:
        return RedirectResponse(request.url_for("no_data"), status_code=status.HTTP_302_FOUND)
    except Exception as e:
        logger.error(f"Failed to get student {student_id} stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.get("/get_image/{student_id}", name="get_image")
async def get_image(
    student_id: int,
    crud: StudentDBHandler = Depends(get_student_crud),
):
    achievement = await get_achievement_for_student(crud, student_id)
    image_data = await get_image_data(achievement, orientation="vertical")
    image_bytes, content_type, filename = await fetch_image(image_data["url"])

    return Response(
        content=image_bytes,
        media_type=content_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/h/{student_id}", name="share_horizontal")
@router.get("/v/{student_id}", name="share_vertical")
@router.get("/vk/{student_id}", name="share_vk")
async def share(
    request: Request,
    student_id: int,
    crud: StudentDBHandler = Depends(get_student_crud),
):
    orientation = get_orientation(request)
    achievement = await get_achievement_for_student(crud, student_id)
    image_data = await get_image_data(achievement, orientation)

    if is_social_bot(request):
        return templates.TemplateResponse(
            "share.html",
            {
                "request": request,
                "student_id": student_id,
                "title": "Мой стиль и статистика обучения",
                "description": "Внутри подарок от Skypro",
                "achievement_url": image_data["url"],
                "image_width": image_data["width"],
                "image_height": image_data["height"],
                "base_url": HOST_URL,
            },
        )

    return add_no_cache_headers(
        RedirectResponse(request.url_for("referal", student_id=student_id), status_code=status.HTTP_302_FOUND)
    )


@router.get("/tg/{student_id}", name="tg")
async def tg(
    request: Request,
    student_id: int,
    background_tasks: BackgroundTasks,
    crud: StudentDBHandler = Depends(get_student_crud),
):
    achievement = await get_achievement_for_student(crud, student_id)
    image_data = await get_image_data(achievement, orientation="vertical")

    if IS_HEROKU:  # noqa SIM108
        referal_url = f"{HOST_URL}/s/{student_id}"
    else:
        referal_url = str(request.url_for("referal", student_id=student_id))

    background_tasks.add_task(send_telegram_updates, image_data["url"], referal_url)

    return add_no_cache_headers(RedirectResponse(settings.TG_CHANNEL, status_code=status.HTTP_302_FOUND))


@router.get("/s/{student_id}", name="referal")
async def referal(
    request: Request,
    student_id: int,
    crud: StudentDBHandler = Depends(get_student_crud),
):
    achievement = await get_achievement_for_student(crud, student_id)
    student = await get_student_by_id(crud, student_id)

    context = {
        "request": request,
        "student_id": student.id,
        "first_name": student.first_name,
        "last_name": student.last_name,
        "days_since_start": student.days_since_start,
        "profession": student.profession.value,
        "profession_info": student.profession_info,
        "profession_dative": student.profession.dative,
        "skills": get_student_skills(student),
        "title": achievement.title,
        "description": achievement.description,
        "achievement_logo": get_achievement_logo_relative_path(achievement),
        **get_stats(student),
    }

    return add_no_cache_headers(templates.TemplateResponse("referal.html", context))


async def process_url_submission(data: URLSubmission):
    success = await sheet_pusher.push_data_to_sheet(data)
    if not success:
        logger.error(f"Failed to submit student {data.student_id} data to Google Sheet. Save for retry later.")
        await sheet_pusher.save_failed_submission(data)
    else:
        logger.info(f"Data submitted to Google Sheet for student {data.student_id}")


@router.post("/submit-url")
async def submit_url(data: URLSubmission, background_tasks: BackgroundTasks):
    background_tasks.add_task(process_url_submission, data)
    return JSONResponse({"status": "processing"})


@router.post("/submit-phone")
async def submit_phone(data: PhoneSubmission):
    # TODO: Has to refactor it (move logic to crm_service.py)
    url = settings.CRM_URL
    payload = {
        "phone": f"{data.phone}",
        "funnel": "direct",
        "sourceKey": "sharestats",
        "name": "Заявка на Карьерную Консультацию",
        "productId": 191,
        "utmTerm": f"referral-{data.student_id}",
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                result = await response.text()
                logger.info(f"Phone {data.phone}, ref to student {data.student_id}. Result: {result}")
    except Exception as e:
        logger.error(f"Did not submit phone to CRM. Error: {e}")
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/results", name="results")
async def top_achievements(request: Request, crud: StudentDBHandler = Depends(get_student_crud)):
    counts_of_received_achievements: list[tuple[str, str, int]] = await crud.get_list_of_achievements_received()
    achievements = await get_achievements_data(counts_of_received_achievements)
    return templates.TemplateResponse("results.html", {"request": request, "achievements": achievements})


@router.get("/dashboard", name="dashboard")
async def dashboard():
    return RedirectResponse(STUDENT_DASHBOARD, status_code=status.HTTP_308_PERMANENT_REDIRECT)


@router.get("/no_data", name="no_data")
async def no_data(request: Request):
    return templates.TemplateResponse("no_data.html", {"request": request})
