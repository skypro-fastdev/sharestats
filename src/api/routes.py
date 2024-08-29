from fastapi import APIRouter, Depends, Security, status
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import APIKeyHeader

from src.config import settings
from src.db.students_crud import StudentDBHandler, get_student_crud
from src.models import DateQuery, Purchase
from src.services.export_csv import generate_csv

api_key_header = APIKeyHeader(name="X-API-Key")


async def validate_token(key: str = Security(api_key_header)):
    if key != settings.API_KEY:
        return JSONResponse({"message": "Invalid API key"}, status_code=status.HTTP_403_FORBIDDEN)
    return None


api_router = APIRouter(dependencies=[Depends(validate_token)])


@api_router.post("/bonuses/purchase")
async def purchase_product(data: Purchase):
    return JSONResponse(
        {
            "message": f"Product {data.product_id} purchased by student {data.student_id}",
            "status": "OK",
        },
        status_code=status.HTTP_200_OK,
    )


@api_router.post("/export/csv", name="export_csv")
async def get_last_login_csv(
    date_query: DateQuery = Depends(),
    crud: StudentDBHandler = Depends(get_student_crud),
):
    students = await crud.get_students_with_last_login(date_query.search_date)

    return StreamingResponse(
        iter([generate_csv(students).getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=students_last_login_{date_query.formatted_date}.csv"},
    )
