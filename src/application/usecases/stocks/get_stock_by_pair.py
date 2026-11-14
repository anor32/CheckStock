"""Get stock by product and warehouse use case."""

from __future__ import annotations

from src.application.dtos import StockListItemDTO
from src.domain.interfaces import IUnitOfWork


class GetStockByPairUseCase:
    def __init__(self, uow: IUnitOfWork) -> None:
        self.uow = uow

    async def execute(self, product_id: int, warehouse_id: int) -> StockListItemDTO:
        product, stock, warehouse = await self.uow.stock_repo.get_by_product_and_warehouse(
            product_id, warehouse_id
        )
        return StockListItemDTO.from_entities(product, stock, warehouse)
