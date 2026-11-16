"""Soft-delete warehouse use case."""

from __future__ import annotations

from src.domain.entities import Warehouse
from src.domain.exceptions import WarehouseHasActiveMovementsError
from src.domain.interfaces import IUnitOfWork


class DeleteWarehouseUseCase:
    def __init__(self, uow: IUnitOfWork) -> None:
        self.uow = uow

    async def execute(self, warehouse_id: int) -> Warehouse:
        warehouse = await self.uow.warehouse_repo.get_by_id(warehouse_id, include_deleted=True)
        if not warehouse.is_deleted:
            if await self.uow.movement_repo.has_unfinished_for_warehouse(warehouse_id):
                raise WarehouseHasActiveMovementsError(
                    f"Cannot delete warehouse {warehouse_id}: there are unfinished movements"
                )
            warehouse.mark_deleted()
            warehouse = await self.uow.warehouse_repo.update(warehouse)
        return warehouse
