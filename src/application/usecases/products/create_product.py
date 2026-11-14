from __future__ import annotations

from src.application.dtos import CreateProductDTO
from src.domain.entities import Product
from src.domain.interfaces import IUnitOfWork


class CreateProductUseCase:
    def __init__(self, uow: IUnitOfWork) -> None:
        self.uow = uow

    async def execute(self, input_data: CreateProductDTO) -> Product:
        return await self.uow.sku_repo.add(input_data)
