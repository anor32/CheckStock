"""Receive transfer movement use case."""

from __future__ import annotations

from src.application.dtos import CreateStockDTO, ReceiveMovementInput
from src.domain.entities import Movement, MovementType, Stock
from src.domain.exceptions import StockNotFoundError
from src.domain.interfaces import IUnitOfWork


class ReceiveMovementUseCase:
    def __init__(self, uow: IUnitOfWork) -> None:
        self.uow = uow

    async def execute(self, input_data: ReceiveMovementInput) -> Movement:
        movement = await self.uow.movement_repo.get_movement(input_data.movement_id)
        movement.ensure_type(MovementType.TRANSFER_OUT)
        if movement.is_completed():
            return movement

        to_warehouse_id = movement.ensure_to_warehouse_id()
        await self._ensure_active_warehouse(to_warehouse_id)
        to_stock = await self._get_or_create_stock(movement.product_id, to_warehouse_id)
        to_stock.receive(movement.qty)
        await self.uow.stock_repo.update(to_stock)

        movement.complete()
        return await self.uow.movement_repo.save_movement(movement)

    async def _ensure_active_warehouse(self, warehouse_id: int) -> None:
        warehouse = await self.uow.warehouse_repo.get_by_id(warehouse_id)
        warehouse.ensure_active()

    async def _get_or_create_stock(self, product_id: int, warehouse_id: int) -> Stock:
        try:
            _, stock, _ = await self.uow.stock_repo.get_by_product_and_warehouse_for_update(
                product_id, warehouse_id
            )
        except StockNotFoundError:
            return await self.uow.stock_repo.create(
                CreateStockDTO(product_id=product_id, warehouse_id=warehouse_id)
            )
        else:
            return stock
