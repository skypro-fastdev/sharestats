import json

import aiohttp
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.requests import Request
from fastapi.responses import JSONResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from loguru import logger

from src.bot.logger import tg_logger
from src.config import IS_HEROKU, settings
from src.db.students_crud import StudentDBHandler, get_student_crud
from src.dependencies import data_cache, sheet_pusher
from src.models import CRMSubmission, URLSubmission
from src.services.images import fetch_image, get_achievement_logo_relative_path, get_image_data
from src.services.security import verify_hash_dependency
from src.services.stats import get_achievements_data, get_meme_stats, get_stats, get_student_skills
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
    hash_verified: None = Depends(verify_hash_dependency),
    handler: StudentHandler = Depends(get_student_handler),
    crud: StudentDBHandler = Depends(get_student_crud),
):
    try:
        student = await get_student_data(handler, student_id)
        db_student = await update_or_create_student_in_db(crud, student)
        db_achievement = await update_or_create_achievement_in_db(crud, handler.achievement)
        await crud.add_achievement_to_student(db_student.id, db_achievement.id)

        meme_stats = get_meme_stats(json.loads(db_student.meme_stats))

        context = {
            "request": request,
            "student_id": student.id,
            "student_name": f"{student.first_name} {student.last_name}",
            "days_since_start": student.days_since_start,
            "months_since_start": student.months_since_start,
            "profession": student.profession.value,
            "skills": get_student_skills(student),
            "title": handler.achievement.title,
            "description": handler.achievement.description,
            "achievement_logo": get_achievement_logo_relative_path(handler.achievement),
            "schedule_title": "Мой график",
            "meme_stats": meme_stats,
            "tg_link": settings.TG_CHANNEL,
            "base_url": HOST_URL,
            **get_stats(student),
        }

        return add_no_cache_headers(templates.TemplateResponse("stats.html", context))

    except NoDataException:
        return RedirectResponse(request.url_for("no_data"), status_code=status.HTTP_302_FOUND)

    except HTTPException as http_ex:
        raise http_ex

    except Exception as e:
        logger.error(f"Failed to get student {student_id} stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.get("/get_image/{student_id}", name="get_image")
async def get_image(
    request: Request,
    student_id: int,
    crud: StudentDBHandler = Depends(get_student_crud),
):
    achievement = await get_achievement_for_student(crud, student_id, endpoint=request.url.path)
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
    achievement = await get_achievement_for_student(crud, student_id, endpoint=request.url.path)
    image_data = await get_image_data(achievement, orientation)

    title = "Посмотрите мои результаты + пройдите бесплатный тест “Какая IT-профессия идеально подойдет вам”"

    if is_social_bot(request):
        return templates.TemplateResponse(
            "share.html",
            {
                "request": request,
                "student_id": student_id,
                "title": title,
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
    achievement = await get_achievement_for_student(crud, student_id, endpoint=request.url.path)
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
    achievement = await get_achievement_for_student(crud, student_id, request.url.path)
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
        "schedule_title": "График обучения",
        "meme_stats": get_meme_stats(student.meme_stats),
        "skills": get_student_skills(student),
        "achievement_title": achievement.title,
        "description": achievement.description,
        "achievement_logo": get_achievement_logo_relative_path(achievement),
        **get_stats(student),
    }

    return add_no_cache_headers(templates.TemplateResponse("referal.html", context))


async def process_submission(data: URLSubmission | CRMSubmission):
    if isinstance(data, URLSubmission):
        worksheet_name = "shared"
    elif isinstance(data, CRMSubmission):
        worksheet_name = "requested_cc" if data.order == "consultation" else "requested_course"
    else:
        raise ValueError("Unknown submission type")

    success = await sheet_pusher.push_data_to_sheet(data, worksheet_name)
    if not success:
        logger.error(f"Failed to submit data to sheet '{worksheet_name}'. Save for retry later.")
        await sheet_pusher.save_failed_submission(data, worksheet_name)


@router.post("/submit-url")
async def submit_url(data: URLSubmission, background_tasks: BackgroundTasks):
    background_tasks.add_task(process_submission, data)
    return JSONResponse({"status": "processing"})


# /submit-to-crm DEPRECATED
@router.post("/submit-to-crm", name="submit_to_crm")
async def submit_to_crm(data: CRMSubmission, background_tasks: BackgroundTasks):
    # TODO: Has to refactor it (move logic to crm_service.py)
    background_tasks.add_task(process_submission, data)

    url = settings.CRM_URL

    if not data.phone or not data.order:
        return JSONResponse(content={"status": "error", "message": "Необходимо заполнить все поля!"}, status_code=400)

    payload = {
        "phone": data.phone,
        "funnel": "direct",
        "sourceKey": "sharestats",
        "name": "Заявка на Карьерную Консультацию"
        if data.order == "consultation"
        else "Заявка на получение мини-курса",
        "productId": 191,
        "utmTerm": f"referral-{data.student_id}",
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    logger.error(
                        f"Failed to submit phone {data.phone}, order {data.order} to CRM. Status: {response.status}"
                    )
                    raise HTTPException(status_code=response.status, detail="CRM request failed")

                crm_answer = await response.text()
                logger.info(
                    f"Submitted phone {data.phone}, order {data.order}, "
                    f"ref to student {data.student_id}. Answer from CRM: {crm_answer}"
                )
                return JSONResponse(content={"status": "success"}, status_code=200)
    except aiohttp.ClientError as e:
        logger.error(f"Failed to submit phone {data.phone}, order {data.order} to CRM. Error: {e}")
        raise HTTPException(status_code=503, detail="Something went wrong") from e
    except Exception as e:
        logger.error(f"Unexpected error when submitting phone {data.phone}, order {data.order} to CRM. Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error") from e


@router.get("/results", name="results")
async def top_achievements(request: Request, crud: StudentDBHandler = Depends(get_student_crud)):
    counts_of_received_achievements = await crud.get_list_of_achievements_received()
    achievements = await get_achievements_data(counts_of_received_achievements)
    return templates.TemplateResponse("results.html", {"request": request, "achievements": achievements})


@router.get("/dashboard", name="dashboard")
async def dashboard():
    return RedirectResponse(STUDENT_DASHBOARD, status_code=status.HTTP_308_PERMANENT_REDIRECT)


@router.get("/no_data", name="no_data")
async def no_data(request: Request):
    return templates.TemplateResponse("no_data.html", {"request": request})


@router.get("/quiz/{student_id}", name="quiz")
async def meme_quiz(
    request: Request,
    student_id: int,
):
    context = {
        "request": request,
        "student_id": student_id,
        "questions": data_cache.meme_data.values(),
    }
    return templates.TemplateResponse("meme-quiz.html", context)


@router.post("/quiz", name="quiz_result")
async def meme_quiz_result(
    request: Request,
    crud: StudentDBHandler = Depends(get_student_crud),
):
    try:
        answers = await request.json()
        student_id = int(answers.pop("student_id"))

        meme_stats = {}
        for meme_id, option_index in answers.items():
            meme_stats[meme_id] = data_cache.meme_data[meme_id].options[option_index]

        result = await crud.add_meme_stats_to_student(student_id, meme_stats)

        if not result:
            logger.error(f"Failed to add meme stats to student {student_id}")
            await tg_logger.log("ERROR", f"Failed to add meme stats to student {student_id}")
            raise HTTPException(status_code=500, detail="Failed to add meme stats to student")

        return JSONResponse(
            content={"status": "success", "message": "Ответы успешно получены. Статистика обновлена"},
            status_code=200,
        )
    except json.JSONDecodeError:
        logger.error("Invalid JSON data received from the request.")
        raise HTTPException(status_code=400, detail="Invalid JSON data received from the request.") from None
    except Exception as e:
        logger.error(f"Error processing quiz answers: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error") from e
