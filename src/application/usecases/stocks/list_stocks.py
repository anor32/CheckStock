"""List stocks use case."""

from __future__ import annotations

from src.application.dtos import ListStocksQuery, PaginatedStocksDTO
from src.domain.interfaces import IUnitOfWork


class ListStocksUseCase:
    def __init__(self, uow: IUnitOfWork) -> None:
        self.uow = uow

    async def execute(self, query: ListStocksQuery) -> PaginatedStocksDTO:
        items, total = await self.uow.stock_repo.list_stocks(query)
        return PaginatedStocksDTO(
            items=items,
            total=total,
            page=query.pagination.page,
            page_size=query.pagination.page_size,
        )
