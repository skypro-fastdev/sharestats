from typing import Sequence

from fastapi import HTTPException, status
from sqlalchemy import Row, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import not_, select

from src.db.models import ProductDB, StudentChallenge, StudentDB, StudentProduct
from src.models import Purchase


async def process_purchase(session: AsyncSession, data: Purchase) -> StudentProduct:
    async with session.begin():
        # Получаем продукт
        query = select(ProductDB).where(ProductDB.id == data.product_id, ProductDB.is_active == True)  # noqa
        result = await session.execute(query)
        product = result.scalar_one_or_none()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"status": "error", "message": f"Продукт {data.product_id} не существует либо не активен"},
            )

        # Получаем студента
        query = select(StudentDB).where(StudentDB.id == data.student_id)
        result = await session.execute(query)
        student = result.scalar_one_or_none()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"status": "error", "message": f"Студент с ID {data.student_id} не найден"},
            )

        # Проверяем, не куплен ли уже этот продукт
        query = select(StudentProduct).where(
            StudentProduct.student_id == data.student_id, StudentProduct.product_id == data.product_id
        )
        result = await session.execute(query)
        existing_purchase = result.scalar_one_or_none()
        if existing_purchase:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"status": "error", "message": f"Студент уже приобрел продукт с ID {data.product_id}"},
            )

        # Проверяем баланс
        if student.points < product.value:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={
                    "status": "error",
                    "message": f"Недостаточно бонусов для покупки. "
                    f"Требуется: {product.value}, доступно: {student.points}",
                },
            )

        # Создаем запись о покупке
        new_purchase = StudentProduct(**data.model_dump(exclude={"created_at"}))
        session.add(new_purchase)

        # Обновляем баланс студента
        student.points -= product.value

        # Сохраняем изменения
        await session.flush()
        return new_purchase


async def get_purchased_products_and_challenges(
    session: AsyncSession,
) -> Sequence[Row]:
    query = (
        select(
            StudentDB.id,
            StudentDB.bonuses_last_visited,
            func.count(func.distinct(StudentChallenge.challenge_id)).label("completed_challenges"),
            func.count(func.distinct(StudentProduct.product_id)).label("purchased_products"),
        )
        .outerjoin(StudentChallenge)
        .outerjoin(StudentProduct)
        .where(not_(StudentDB.bonuses_last_visited.is_(None)))
        .group_by(StudentDB.id, StudentDB.bonuses_last_visited)
        .order_by(StudentDB.id)
    )

    results = await session.execute(query)
    return results.all()
