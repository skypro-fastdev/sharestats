from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.db.challenges_crud import ChallengeDBHandler, get_challenge_crud
from src.db.products_crud import ProductDBHandler, get_product_crud
from src.db.session import get_async_session
from src.db.students_crud import StudentDBHandler, get_student_crud
from src.models import Challenge, DateQuery, Product, Purchase
from src.services.export_csv import generate_csv
from src.services.purchases import process_purchase

api_key_header = APIKeyHeader(name="X-API-Key")


async def validate_token(key: str = Security(api_key_header)):
    if key != settings.API_KEY:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)


api_router = APIRouter(dependencies=[Depends(validate_token)])


@api_router.post("/bonuses/challenges", name="challenges")
@api_router.put("/bonuses/challenges", name="challenges_update")
async def process_challenges(
    data: list[Challenge],
    crud: ChallengeDBHandler = Depends(get_challenge_crud),
):
    try:
        results = await crud.process_challenges_batch(data)

        return JSONResponse(
            {"status": "OK", "message": "Challenges processed", "results": results},
            status_code=status.HTTP_200_OK,
        )
    except Exception as e:
        return JSONResponse(
            content={"status": "error", "message": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_router.put("/bonuses/products", name="products")
@api_router.post("/bonuses/products", name="products_update")
async def process_products(
    data: list[Product],
    crud: ProductDBHandler = Depends(get_product_crud),
):
    try:
        results = await crud.process_products_batch(data)
        return JSONResponse(
            {"status": "OK", "message": "Products processed", "results": results},
            status_code=status.HTTP_200_OK,
        )
    except Exception as e:
        return JSONResponse(
            content={"status": "error", "message": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_router.post("/bonuses/purchases", name="purchases")
async def process_purchases(
    data: Purchase,
    session: AsyncSession = Depends(get_async_session),
):
    try:
        purchase = await process_purchase(session, data)
        return JSONResponse(
            {"id": purchase.id, "created_at": purchase.created_at.isoformat()},
            status_code=status.HTTP_201_CREATED,
        )
    except HTTPException as e:
        return JSONResponse(content=e.detail, status_code=e.status_code)
    except Exception as e:
        return JSONResponse(
            content={"status": "error", "message": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
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
