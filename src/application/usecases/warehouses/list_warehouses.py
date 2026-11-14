"""List warehouses use case."""

from __future__ import annotations

from src.application.dtos import ListWarehousesQuery, WarehouseDTO
from src.domain.interfaces import IUnitOfWork


class ListWarehousesUseCase:
    def __init__(self, uow: IUnitOfWork) -> None:
        self.uow = uow

    async def execute(self, query: ListWarehousesQuery) -> list[WarehouseDTO]:
        warehouses = await self.uow.warehouse_repo.list_all(include_deleted=query.include_deleted)
        return [WarehouseDTO.from_entity(w) for w in warehouses]
