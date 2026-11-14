"""Soft-delete warehouse use case."""

from __future__ import annotations

from src.domain.entities import Warehouse
from src.domain.interfaces import IUnitOfWork


class DeleteWarehouseUseCase:
    def __init__(self, uow: IUnitOfWork) -> None:
        self.uow = uow

    async def execute(self, warehouse_id: int) -> Warehouse:
        warehouse = await self.uow.warehouse_repo.get_by_id(warehouse_id, include_deleted=True)
        if not warehouse.is_deleted:
            warehouse.mark_deleted()
            warehouse = await self.uow.warehouse_repo.update(warehouse)
        return warehouse
