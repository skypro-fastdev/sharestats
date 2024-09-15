from typing import Sequence

from fastapi import Depends
from loguru import logger
from sqlalchemy import Row
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlmodel import select

from src.db.models import ProductDB, StudentProduct
from src.db.session import get_async_session
from src.models import Product


class ProductDBHandler:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_product(self, product_id: str, active_only: bool = False) -> ProductDB | None:
        query = select(ProductDB).where(ProductDB.id == product_id)
        if active_only:
            query = query.where(ProductDB.is_active == True)  # noqa
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all_products(self, active_only: bool = False) -> list[ProductDB]:
        query = select(ProductDB)
        if active_only:
            query = query.where(ProductDB.is_active == True)  # noqa
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create_product(self, product: Product) -> ProductDB | None:
        try:
            db_product = ProductDB(**product.model_dump())
            self.session.add(db_product)
            await self.session.commit()
            await self.session.refresh(db_product)
            logger.info(f"Created product {db_product.id}")
            return db_product
        except Exception as e:
            logger.error(f"Failed to create product: {e}")
            await self.session.rollback()
            return None

    async def update_product(self, product: Product) -> ProductDB | None:
        db_product = await self.get_product(product.id)
        if not db_product:
            return None

        try:
            for key, value in product.model_dump().items():
                setattr(db_product, key, value)

            await self.session.commit()
            await self.session.refresh(db_product)
            logger.info(f"Updated product {db_product.id}")
            return db_product
        except Exception as e:
            logger.error(f"Failed to update product {db_product.id}: {e}")
            await self.session.rollback()
            return None

    async def process_products_batch(self, products: list[Product]) -> dict:
        results = {"created": 0, "updated": 0, "unchanged": 0, "failed": 0}

        for product in products:
            try:
                existing_product = await self.get_product(product.id)

                if existing_product is None:
                    new_product = await self.create_product(product)
                    if new_product:
                        results["created"] += 1
                    else:
                        results["failed"] += 1
                elif (
                    existing_product.is_active != product.is_active
                    or existing_product.title != product.title
                    or existing_product.description != product.description
                    or existing_product.value != product.value
                ):
                    updated_product = await self.update_product(product)
                    if updated_product:
                        results["updated"] += 1
                    else:
                        results["failed"] += 1
                else:
                    results["unchanged"] += 1
            except Exception as e:
                logger.error(f"Failed to process product {product.id}: {e}")
                results["failed"] += 1

        return results

    async def get_purchased_products(self, student_id: int) -> list[StudentProduct]:
        query = (
            select(StudentProduct)
            .options(joinedload(StudentProduct.product))
            .where(StudentProduct.student_id == student_id)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_all_purchased_products(self) -> Sequence[Row]:
        query = select(
            StudentProduct.student_id, StudentProduct.product_id, StudentProduct.created_at, StudentProduct.added_by
        )
        result = await self.session.execute(query)
        return result.all()


async def get_product_crud(session: AsyncSession = Depends(get_async_session)) -> ProductDBHandler:
    return ProductDBHandler(session)
