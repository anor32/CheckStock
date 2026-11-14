from __future__ import annotations

from src.application.dtos import ProductDTO
from src.domain.interfaces import IUnitOfWork


class ListProductsUseCase:
    def __init__(self, uow: IUnitOfWork) -> None:
        self.uow = uow

    async def execute(self) -> list[ProductDTO]:
        products = await self.uow.sku_repo.list_all()
        return [ProductDTO.from_entity(p) for p in products]
