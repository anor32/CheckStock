"""List movements use case."""

from __future__ import annotations

from src.application.dtos import ListMovementsDTO, PaginatedMovementsDTO
from src.domain.interfaces import IUnitOfWork


class ListMovementsUseCase:
    def __init__(self, uow: IUnitOfWork) -> None:
        self.uow = uow

    async def execute(self, query: ListMovementsDTO) -> PaginatedMovementsDTO:
        rows, total = await self.uow.movement_repo.list_movements(query)
        return PaginatedMovementsDTO(
            items=rows,
            total=total,
            page=query.pagination.page,
            page_size=query.pagination.page_size,
        )
