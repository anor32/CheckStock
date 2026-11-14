"""Update (rename) warehouse use case."""

from __future__ import annotations

from src.application.dtos import UpdateWarehouseInput
from src.domain.entities import Warehouse
from src.domain.interfaces import IUnitOfWork


class UpdateWarehouseUseCase:
    def __init__(self, uow: IUnitOfWork) -> None:
        self.uow = uow

    async def execute(self, input_data: UpdateWarehouseInput) -> Warehouse:
        warehouse = await self.uow.warehouse_repo.get_by_id(input_data.warehouse_id)
        warehouse.name = input_data.name
        return await self.uow.warehouse_repo.update(warehouse)
