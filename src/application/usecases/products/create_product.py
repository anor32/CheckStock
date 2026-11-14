from __future__ import annotations

from src.application.dtos import CreateProductInput, ProductDTO
from src.domain.entities import Product
from src.domain.interfaces import IUnitOfWork


class CreateProductUseCase:
    def __init__(self, uow: IUnitOfWork) -> None:
        self.uow = uow

    async def execute(self, input_data: CreateProductInput) -> ProductDTO:
        product = Product(
            id=None,
            sku=input_data.sku,
            name=input_data.name,
            idempotency_key=input_data.idempotency_key,
        )
        saved = await self.uow.sku_repo.add(product)
        return ProductDTO.from_entity(saved)
