from fastapi import APIRouter, Depends, HTTPException
from fastapi.requests import Request
from fastapi.templating import Jinja2Templates
from loguru import logger

from src.config import IS_HEROKU
from src.db.challenges_crud import ChallengeDBHandler, get_challenge_crud
from src.db.products_crud import ProductDBHandler, get_product_crud
from src.db.students_crud import StudentDBHandler, get_student_crud
from src.services.challenges import get_or_create_student
from src.web.handlers import StudentHandler, get_student_handler
from src.web.utils import add_no_cache_headers

router = APIRouter()

templates = Jinja2Templates(directory="src/templates")

HOST_URL = "https://sky.pro/share" if IS_HEROKU else "http://127.0.0.1:8000/share"


@router.get("/bonuses/{student_id}", name="bonuses")
async def bonuses(  # noqa: PLR0913
    request: Request,
    student_id: int,
    hash: str | None = None,  # noqa: A002
    handler: StudentHandler = Depends(get_student_handler),
    students_crud: StudentDBHandler = Depends(get_student_crud),
    challenges_crud: ChallengeDBHandler = Depends(get_challenge_crud),
    products_crud: ProductDBHandler = Depends(get_product_crud),
):
    # if not verify_hash(student_id, hash):
    #     raise HTTPException(status_code=404, detail="Страница не найдена")
    try:
        student, available_challenges, completed_challenges = await get_or_create_student(
            student_id, handler, students_crud, challenges_crud
        )

        available_products = await products_crud.get_all_products()
        purchased_products = await products_crud.get_purchased_products(student_id)

        purchased_product_ids = {purchase.product_id for purchase in purchased_products}

        filtered_available_products = [
            product for product in available_products if product.id not in purchased_product_ids
        ]

        context = {
            "request": request,
            "fullname": f"{student.first_name} {student.last_name}",
            "points": student.points,
            "student_id": student_id,
            "completed_challenges": completed_challenges,
            "available_challenges": available_challenges,
            "available_products": filtered_available_products,
            "purchases": purchased_products,
        }
        return add_no_cache_headers(templates.TemplateResponse("bonuses.html", context))

    except HTTPException as http_ex:
        raise http_ex

    except Exception as e:
        logger.error(f"Failed to get student {student_id} challenges: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") from e
