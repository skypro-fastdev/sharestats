from datetime import datetime

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
from src.services.images import find_or_generate_image, get_achievement_logo_relative_path
from src.services.security import verify_hash
from src.services.stats import get_achievements_data, get_stats, get_student_skills
from src.services.telegram import send_telegram_updates
from src.web.handlers import StudentHandler, get_student_handler

router = APIRouter()

templates = Jinja2Templates(directory="src/templates")

HOST_URL = "https://sky.pro/share" if IS_HEROKU else "http://127.0.0.1:8000/share"
STUDENT_DASHBOARD = "https://my.sky.pro/student-cabinet/"


def is_social_bot(request):
    user_agent = request.headers.get("User-Agent", "").lower()
    referer = request.headers.get("Referer", "")

    bots = ("telegrambot", "instagram", "facebookexternalhit", "linkedinbot", "vkshare")  # 'twitterbot'
    social_referers = ("instagram.com", "facebook.com", "t.co", "t.me", "linkedin.com")  # 'twitter.com', 'vk.com'

    is_bot = any(bot in user_agent for bot in bots)
    is_social_referer = any(social in referer for social in social_referers)
    is_facebook_preview = request.headers.get("X-Purpose") == "preview"

    return is_bot or is_social_referer or is_facebook_preview


@router.get("/stats/{student_id}", name="stats")
async def stats(  # noqa: PLR0912
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

    if not handler.student:
        logger.info(f"Statistics for student {student_id} not found")
        raise HTTPException(status_code=404, detail="Страница не найдена")

    if not handler.achievement:
        logger.info(f"Student {student_id} has no achievement")
        raise HTTPException(status_code=404, detail="Страница не найдена")
    try:
        homework_total = handler.student.statistics.get("homework_total")
        started_at = handler.student.started_at
        today = datetime.today().date()

        if homework_total == 0 or started_at > today:
            return RedirectResponse(request.url_for("no_data"), status_code=status.HTTP_302_FOUND)

        achievement_logo = get_achievement_logo_relative_path(handler.achievement)
    except Exception as e:
        logger.error(f"Failed to get student {student_id} stats: {e}")
        return RedirectResponse(request.url_for("no_data"), status_code=status.HTTP_302_FOUND)

    student_stats = get_stats(handler.student)
    skills = get_student_skills(handler.student)

    db_student = await crud.get_student(student_id)
    if db_student:
        # Если студент существует, обновляем его статистику в БД
        db_student = await crud.update_student(handler.student)
        if not db_student:
            raise HTTPException(status_code=500, detail="Failed to update student statistics in DB")
    else:
        # Если студента нет, создаем нового
        db_student = await crud.create_student(handler.student)
        if not db_student:
            raise HTTPException(status_code=500, detail="Failed to create student in DB")

    # Получаем или создаем достижение
    db_achievement = await crud.get_achievement_by_title_and_profession(
        handler.achievement.title, handler.achievement.profession
    )
    if not db_achievement:
        db_achievement = await crud.create_achievement(handler.achievement)
    if not db_achievement:
        raise HTTPException(status_code=500, detail="Failed to create achievement")

    await crud.add_achievement_to_student(db_student.id, db_achievement.id)

    context = {
        "request": request,
        "student_id": handler.student.id,
        "student_name": f"{handler.student.first_name} {handler.student.last_name}",
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

    response = templates.TemplateResponse("stats.html", context)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@router.get("/get_image/{student_id}", name="get_image")
async def get_image(
    student_id: int,
    crud: StudentDBHandler = Depends(get_student_crud),
):
    db_achievement = await crud.get_achievement_by_student_id(student_id)

    if not db_achievement:
        raise HTTPException(status_code=404, detail="Страница не найдена")

    achievement = db_achievement.to_achievement_model()
    image_data = await find_or_generate_image(achievement, "vertical")

    if not image_data:
        logger.error(f"Failed to get image, student_id: {student_id}")
        raise HTTPException(status_code=500, detail="Failed to get image")

    image_url = image_data["url"]

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(image_url) as response:
                if response.status != 200:
                    raise HTTPException(status_code=500, detail="Failed to fetch image")

                image_bytes = await response.read()
                filename = image_url.split("/")[-1]

                return Response(
                    content=image_bytes,
                    media_type=response.headers.get("Content-Type", "image/png"),
                    headers={"Content-Disposition": f"attachment; filename={filename}"},
                )
        except Exception as e:
            logger.error(f"Failed to fetch image: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to fetch image") from e


@router.get("/h/{student_id}", name="share_horizontal")
@router.get("/v/{student_id}", name="share_vertical")
@router.get("/vk/{student_id}", name="share_vk")
async def share(
    request: Request,
    student_id: int,
    crud: StudentDBHandler = Depends(get_student_crud),
):
    if "/vk/" in request.url.path:
        orientation = "vk_post"
    elif "/h/" in request.url.path:
        orientation = "horizontal"
    else:
        orientation = "vertical"

    db_achievement = await crud.get_achievement_by_student_id(student_id)

    if not db_achievement:
        raise HTTPException(status_code=404, detail="Страница не найдена")

    achievement = db_achievement.to_achievement_model()

    image_data = await find_or_generate_image(achievement, orientation)

    if not image_data:
        logger.error(f"Failed to get image, student_id: {student_id}")
        return HTTPException(status_code=500, detail="Failed to get image")

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

    response = RedirectResponse(request.url_for("referal", student_id=student_id), status_code=status.HTTP_302_FOUND)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@router.get("/tg/{student_id}", name="tg")
async def tg(
    request: Request,
    student_id: int,
    background_tasks: BackgroundTasks,
    crud: StudentDBHandler = Depends(get_student_crud),
):
    db_achievement = await crud.get_achievement_by_student_id(student_id)

    if not db_achievement:
        raise HTTPException(status_code=404, detail="Страница не найдена")

    achievement = db_achievement.to_achievement_model()
    image_data = await find_or_generate_image(achievement, "vertical")

    if not image_data:
        logger.error(f"Failed to get image, student_id: {student_id}")
        raise HTTPException(status_code=500, detail="Failed to get image")

    referal_url = f"{HOST_URL}/s/{student_id}" if IS_HEROKU else str(request.url_for("referal", student_id=student_id))

    background_tasks.add_task(send_telegram_updates, image_data["url"], referal_url)

    response = RedirectResponse(settings.TG_CHANNEL, status_code=status.HTTP_302_FOUND)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@router.get("/s/{student_id}", name="referal")
async def referal(
    request: Request,
    student_id: int,
    crud: StudentDBHandler = Depends(get_student_crud),
):
    db_achievement = await crud.get_achievement_by_student_id(student_id)

    if not db_achievement:
        raise HTTPException(status_code=404, detail="Страница не найдена")

    achievement = db_achievement.to_achievement_model()

    db_student = await crud.get_student(student_id)

    if not db_student:
        raise HTTPException(status_code=404, detail="Страница не найдена")

    student = db_student.to_student()

    achievement_logo = get_achievement_logo_relative_path(achievement)

    student_stats = get_stats(student)
    skills = get_student_skills(student)

    context = {
        "request": request,
        "student_id": student.id,
        "first_name": student.first_name,
        "last_name": student.last_name,
        "days_since_start": student.days_since_start,
        "profession": student.profession.value,
        "profession_info": student.profession_info,
        "profession_dative": student.profession.dative,
        "skills": skills,
        "title": achievement.title,
        "description": achievement.description,
        "achievement_logo": achievement_logo,
    }
    context.update(student_stats)

    return templates.TemplateResponse("referal.html", context)


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


# Route just for tests
@router.get("/change/{student_id}/{change_to}", name="change")
async def change(
    request: Request,
    student_id: int,
    change_to: int,
    crud: StudentDBHandler = Depends(get_student_crud),
):
    db_student = await crud.get_student(student_id)
    student = db_student.to_student()
    student_stats = student.statistics
    student_stats["lessons_completed"] = change_to
    updated_student = await crud.update_student(student)
    if updated_student:
        logger.info(f'Changed "lessons_completed" to {change_to} for student {student_id}')

    return RedirectResponse(request.url_for("referal", student_id=student_id), status_code=status.HTTP_302_FOUND)
