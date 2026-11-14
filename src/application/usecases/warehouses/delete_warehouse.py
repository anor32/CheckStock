"""Soft-delete warehouse use case."""

from __future__ import annotations

from src.application.dtos import WarehouseDTO
from src.domain.interfaces import IUnitOfWork


class DeleteWarehouseUseCase:
    def __init__(self, uow: IUnitOfWork) -> None:
        self.uow = uow

    async def execute(self, warehouse_id: int) -> WarehouseDTO:
        warehouse = await self.uow.warehouse_repo.get_by_id(warehouse_id, include_deleted=True)
        if not warehouse.is_deleted:
            warehouse.mark_deleted()
            await self.uow.warehouse_repo.update(warehouse)
        return WarehouseDTO.from_entity(warehouse)
