from __future__ import annotations

from src.domain.entities import Product
from src.domain.interfaces import IUnitOfWork


class ListProductsUseCase:
    def __init__(self, uow: IUnitOfWork) -> None:
        self.uow = uow

    async def execute(self) -> list[Product]:
        return await self.uow.sku_repo.list_all()
