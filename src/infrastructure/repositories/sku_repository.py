from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import Product
from src.domain.exceptions import ProductAlreadyExistsError, ProductNotFoundError
from src.domain.interfaces import ISkuRepository
from src.infrastructure.models import ProductModel


class SqlAlchemySkuRepository(ISkuRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, product_id: int) -> Product:
        res = await self.session.execute(select(ProductModel).where(ProductModel.id == product_id))
        model = res.scalar_one_or_none()
        if model is None:
            raise ProductNotFoundError(f"Product not found: {product_id}")
        return model.to_entity()

    async def get_by_sku(self, sku: str) -> Product:
        res = await self.session.execute(select(ProductModel).where(ProductModel.sku == sku))
        model = res.scalar_one_or_none()
        if model is None:
            raise ProductNotFoundError(f"Product not found: sku={sku}")
        return model.to_entity()

    async def add(self, product: Product) -> Product:
        existing = await self.session.execute(
            select(ProductModel.id).where(ProductModel.sku == product.sku)
        )
        if existing.scalar_one_or_none() is not None:
            raise ProductAlreadyExistsError("Товар с таким SKU уже существует")
        model = ProductModel(sku=product.sku, name=product.name)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return model.to_entity()

    async def list_all(self) -> list[Product]:
        res = await self.session.execute(select(ProductModel).order_by(ProductModel.id))
        return [m.to_entity() for m in res.scalars().all()]
