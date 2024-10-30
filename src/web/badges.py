from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.requests import Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from loguru import logger

from src.config import IS_HEROKU
from src.db.badges_crud import BadgeDBHandler, get_badges_crud
from src.services.images import find_or_generate_image
from src.web.utils import add_no_cache_headers, get_orientation, is_social_bot

router = APIRouter()

templates = Jinja2Templates(directory="src/templates")

HOST_URL = "https://sky.pro/share" if IS_HEROKU else "http://127.0.0.1:8000/share"


@router.get("/b/{badge_id:int}", name="badges")
async def badges(
    request: Request,
    badge_id: int,
    is_friend: bool = Query(False),
    badges_crud: BadgeDBHandler = Depends(get_badges_crud),
):
    try:
        badge = await badges_crud.get_badge_by_id(badge_id)

        if not badge:
            raise HTTPException(status_code=404, detail="Badge not found")

        context = {
            "request": request,
            "badge_id": badge.id,
            "picture": badge.badge_type + ".png",
            "student_name": badge.student_name,
            "student_id": badge.student_id,
            "title": badge.title,
            "description": badge.description,
            "base_url": HOST_URL,
            "is_friend": is_friend,
        }
        return add_no_cache_headers(templates.TemplateResponse("badge.html", context))

    except HTTPException as http_ex:
        raise http_ex

    except Exception as e:
        logger.error(f"Failed to get badge id {badge_id}. Error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.get("/vk/b/{badge_id:int}", name="vk_badge")
@router.get("/tg/b/{badge_id:int}", name="tg_badge")
async def vk_badge(
    request: Request,
    badge_id: int,
    badges_crud: BadgeDBHandler = Depends(get_badges_crud),
):
    orientation = get_orientation(request)
    badge = await badges_crud.get_badge_by_id(badge_id)
    image_data = await find_or_generate_image(badge.to_badge_model(), orientation)

    if is_social_bot(request):
        return templates.TemplateResponse(
            "share_badge.html",
            {
                "request": request,
                "title": badge.title,
                "description": badge.description,
                "badge_id": badge_id,
                "badge_image_url": image_data["url"],
                "image_width": image_data["width"],
                "image_height": image_data["height"],
                "base_url": HOST_URL,
            },
        )

    redirect_url = request.url_for("badges", badge_id=badge_id)
    redirect_url = str(redirect_url) + "?is_friend=true"
    return add_no_cache_headers(RedirectResponse(redirect_url, status_code=status.HTTP_302_FOUND))
