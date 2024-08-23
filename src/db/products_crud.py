from fastapi import Depends
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, update

from src.db.models import ProductDB
from src.db.session import get_async_session
from src.models import Product


class ProductDBHandler:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_product(self, challenge_id: str) -> ProductDB | None:
        result = await self.session.execute(select(ProductDB).where(ProductDB.id == challenge_id))
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

    async def deactivate_product(self, product_id: str) -> None:
        try:
            await self.session.execute(
                update(ProductDB).where(ProductDB.id == product_id).values(is_active=False)
            )
            await self.session.commit()
            logger.info(f"Deactivated product {product_id}")
        except Exception as e:
            logger.error(f"Failed to deactivate product {product_id}: {e}")
            await self.session.rollback()

    async def sync_products(self, data_cache: dict[str, Product]) -> None:
        db_products = await self.get_all_products()
        products_ids = {product.id for product in db_products}

        products_created = 0
        products_updated = 0
        products_deactivated = 0

        for product_id, product in data_cache.items():
            if product_id in products_ids:
                if not data_cache[product_id].is_active:
                    await self.deactivate_product(product_id)
                    products_deactivated += 1
                    continue
                await self.update_product(product)
                products_updated += 1
            elif data_cache[product_id].is_active:
                await self.create_product(product)
                products_created += 1

        # Deactivate inactive products
        for db_product in db_products:
            if db_product.id not in data_cache and db_product.is_active:
                await self.deactivate_product(db_product.id)
                logger.info(f"Product {db_product.id} deactivated in DB")
                products_deactivated += 1

        logger.info(
            f"Synced products: {products_updated} updated, "
            f"{products_created} created, "
            f"{products_deactivated} deactivated"
        )


async def get_product_crud(session: AsyncSession = Depends(get_async_session)) -> ProductDBHandler:
    return ProductDBHandler(session)
