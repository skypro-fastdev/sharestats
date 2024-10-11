from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.db.badges_crud import BadgeDBHandler, get_badges_crud
from src.db.challenges_crud import ChallengeDBHandler, get_challenge_crud
from src.db.products_crud import ProductDBHandler, get_product_crud
from src.db.session import get_async_session
from src.db.students_crud import StudentDBHandler, get_student_crud
from src.models import Badge, Challenge, DateQuery, Product, Purchase
from src.services.export_csv import generate_csv
from src.services.images import find_or_generate_image
from src.services.purchases import get_purchased_products_and_challenges, process_purchase

api_key_header = APIKeyHeader(name="X-API-Key")


async def validate_token(key: str = Security(api_key_header)):
    if key != settings.API_KEY:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)


api_router = APIRouter(dependencies=[Depends(validate_token)])
open_api_router = APIRouter()


@api_router.post(
    "/bonuses/challenges",
    name="challenges",
    summary="Добавить новые челленджи",
    description="Создаёт новые записи о челленджах и возвращает результаты",
)
@api_router.put(
    "/bonuses/challenges",
    name="challenges_update",
    summary="Обновить существующие челленджи",
    description="Обрабатывает список существующих челленджей и возвращает результаты",
)
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


@api_router.put(
    "/bonuses/products",
    name="products",
    summary="Обновить существующие продукты",
    description="Обновляет список существующих продуктов и возвращает результаты.",
)
@api_router.post(
    "/bonuses/products",
    name="products_update",
    summary="Создать новые продукты",
    description="Создаёт новые записи о продуктах и возвращает результаты.",
)
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


@api_router.post(
    "/bonuses/purchases",
    name="purchases",
    summary="Добавить новую покупку",
    description="Создаёт новую запись о покупке и возвращает результаты",
)
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


@api_router.get(
    "/export/csv",
    name="export_csv",
    summary="Экспорт CSV с последними входами пользователей в sharestats",
    description="Формирует CSV-файл с пользователями, которые заходили на страницы со статистикой. "
    "Файл содержит информацию о последнем входе пользователей на указанную дату.",
)
async def get_last_login_csv(
    date_query: DateQuery = Depends(),
    crud: StudentDBHandler = Depends(get_student_crud),
):
    students = await crud.get_students_with_last_login(date_query.search_date)

    return StreamingResponse(
        iter([generate_csv(students, "last_login").getvalue().encode("utf-8-sig")]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=students_last_login_{date_query.formatted_date}.csv",
            "Content-Type": "text/csv; charset=utf-8-sig",
        },
    )


@open_api_router.get(
    "/bonuses/adoption",
    name="adoption",
    summary="Экспорт CSV с данными о выполнении челленджей и покупке продуктов",
    description="Формирует CSV-файл с пользователями, которые хотя бы раз заходили на страницу с бонусами. "
    "Файл содержит информацию о количествах приобретённых продуктов и выполненных челленджах.",
)
async def get_adoption_csv(
    session: AsyncSession = Depends(get_async_session),
):
    data = await get_purchased_products_and_challenges(session)

    return StreamingResponse(
        iter([generate_csv(data, "adoption").getvalue().encode("utf-8-sig")]),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=adoption.csv",
            "Content-Type": "text/csv; charset=utf-8-sig",
        },
    )


@api_router.get(
    "/bonuses/csv",
    name="export_bonuses_csv",
    summary="Экспорт CSV с данными о покупках",
    description="Формирует CSV-файл с покупками. Файл содержит информацию о покупках, "
    "включая ID студента, ID продукта, дату создания и информацию о том, "
    "кем была добавлена покупка для студента.",
)
async def get_purchases_csv(
    crud: ProductDBHandler = Depends(get_product_crud),
):
    data = await crud.get_all_purchased_products()

    return StreamingResponse(
        iter([generate_csv(data, "purchases").getvalue().encode("utf-8-sig")]),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=purchases.csv",
            "Content-Type": "text/csv; charset=utf-8-sig",
        },
    )


@api_router.post(
    "/badges",
    name="badges",
    summary="Добавить новые бейджи",
    description="Стирает таблицу с бейджами и создаёт новые записи с бейджами в БД",
)
async def process_badges(
    data: list[Badge],
    crud: BadgeDBHandler = Depends(get_badges_crud),
):
    try:
        await crud.process_badges_batch(data)
        return JSONResponse(
            {"status": "OK", "message": "Badges processed"},
            status_code=status.HTTP_200_OK,
        )
    except Exception as e:
        return JSONResponse(
            content={"status": "error", "message": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@open_api_router.get(
    "/api/badges/{badge_id}",
    name="badges",
    summary="Получить информацию о бейдже",
    description="Возвращает информацию о бейдже",
)
async def get_badges(badge_id: int, crud: BadgeDBHandler = Depends(get_badges_crud)):
    try:
        badge = await crud.get_badge_by_id(badge_id)
        badge = badge.to_badge_model()
        image_data = await find_or_generate_image(badge, "tg_badge")
        data = badge.model_dump()
        data.update({"sharing_card_url": image_data["url"]})
        return data
    except Exception as e:
        return JSONResponse(
            content={"status": "error", "message": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
