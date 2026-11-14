"""Create warehouse use case."""

from __future__ import annotations

from src.application.dtos import CreateWarehouseDTO
from src.domain.entities import Warehouse
from src.domain.interfaces import IUnitOfWork


class CreateWarehouseUseCase:
    def __init__(self, uow: IUnitOfWork) -> None:
        self.uow = uow

    async def execute(self, input_data: CreateWarehouseDTO) -> Warehouse:
        return await self.uow.warehouse_repo.create(input_data)
