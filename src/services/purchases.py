from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.db.models import ProductDB, StudentDB, StudentProduct
from src.models import Purchase


async def process_purchase(session: AsyncSession, data: Purchase) -> StudentProduct:
    async with session.begin():
        # Получаем продукт
        query = select(ProductDB).where(ProductDB.id == data.product_id, ProductDB.is_active == True)
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

        # Проверяем баланс
        if student.points < product.value:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={
                    "status": "error",
                    "message": f"Недостаточно бонусов для покупки. Требуется: {product.value}, доступно: {student.points}",
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
