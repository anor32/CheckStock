"""List stocks use case."""

from __future__ import annotations

from src.application.dtos import ListStocksQuery, PaginatedStocksDTO
from src.domain.interfaces import IUnitOfWork


class ListStocksUseCase:
    def __init__(self, uow: IUnitOfWork) -> None:
        self.uow = uow

    async def execute(self, query: ListStocksQuery) -> PaginatedStocksDTO:
        normalized_query = ListStocksQuery(
            page=max(1, query.page),
            page_size=max(1, min(100, query.page_size)),
            sku=query.sku,
            warehouse_id=query.warehouse_id,
            include_deleted_warehouses=query.include_deleted_warehouses,
        )
        items, total = await self.uow.stock_repo.list_stocks(normalized_query)
        return PaginatedStocksDTO(
            items=items,
            total=total,
            page=normalized_query.page,
            page_size=normalized_query.page_size,
        )
