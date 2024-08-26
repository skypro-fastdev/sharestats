from fastapi import APIRouter, Depends, HTTPException
from fastapi.requests import Request
from fastapi.templating import Jinja2Templates

from src.config import IS_HEROKU
from src.db.challenges_crud import ChallengeDBHandler, get_challenge_crud
from src.db.products_crud import ProductDBHandler, get_product_crud
from src.db.students_crud import StudentDBHandler, get_student_crud
from src.web.handlers import StudentHandler, get_student_handler

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

    student = await students_crud.get_student_with_challenges(student_id)

    if not student:  # If not found in DB (first time on the site)
        if not handler.student:
            raise HTTPException(status_code=404, detail="Страница не найдена")

        student = await students_crud.create_student(handler.student)
        if not student:
            raise HTTPException(status_code=500, detail="Failed to create a new student in DB")

        # Calculate challenges and add points
        active_challenges, completed_challenges = await challenges_crud.update_new_student_challenges(student)
        student = await students_crud.get_student(student_id)  # Refresh student data

        if not student:
            raise HTTPException(status_code=500, detail="Failed to retrieve updated student data")
    else:
        completed_challenges = [c.challenge for c in student.student_challenges]
        active_challenges = await challenges_crud.get_all_challenges(active_only=True)

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
    return templates.TemplateResponse("bonuses.html", context)
