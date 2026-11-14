"""Create warehouse use case."""

from __future__ import annotations

from src.application.dtos import CreateWarehouseInput, WarehouseDTO
from src.domain.interfaces import IUnitOfWork


class CreateWarehouseUseCase:
    def __init__(self, uow: IUnitOfWork) -> None:
        self.uow = uow

    async def execute(self, input_data: CreateWarehouseInput) -> WarehouseDTO:
        warehouse = input_data.to_entity()
        saved = await self.uow.warehouse_repo.create(warehouse)
        return WarehouseDTO.from_entity(saved)
