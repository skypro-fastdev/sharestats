from fastapi import APIRouter, Depends
from fastapi.requests import Request
from fastapi.templating import Jinja2Templates

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

    student, active_challenges, completed_challenges = await get_or_create_student(
        student_id, handler, students_crud, challenges_crud
    )

    available_challenges = [c for c in active_challenges if c not in completed_challenges]
    available_products = await products_crud.get_all_products()

    context = {
        "request": request,
        "fullname": f"{student.first_name} {student.last_name}",
        "points": student.points,
        "student_id": student_id,
        "completed_challenges": completed_challenges,
        "available_challenges": available_challenges,
        "available_products": available_products,
        "purchased_products": [],
        "active_tab": "earn",
    }
    return add_no_cache_headers(templates.TemplateResponse("bonuses.html", context))
