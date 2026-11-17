"""FBS cancel movement use case."""

from __future__ import annotations

from src.application.dtos import CreateStockDTO, FbsCancelMovementInput
from src.domain.entities import Movement, MovementStatus, MovementType, Stock
from src.domain.exceptions import StockNotFoundError
from src.domain.interfaces import IUnitOfWork


class FbsCancelMovementUseCase:
    def __init__(self, uow: IUnitOfWork) -> None:
        self.uow = uow

    async def execute(self, input_data: FbsCancelMovementInput) -> Movement:
        movement = await self.uow.movement_repo.get_movement_for_update(input_data.movement_id)
        movement.ensure_type(MovementType.FBS_RESERVE)
        if movement.is_cancelled():
            return movement
        movement.ensure_fbs_reserve_pending()

        from_warehouse_id = movement.ensure_from_warehouse_id()
        await self._ensure_active_warehouse(from_warehouse_id)
        stock = await self._get_or_create_stock(movement.product_id, from_warehouse_id)
        stock.release_reservation(movement.qty)
        await self.uow.stock_repo.update(stock)

        movement.complete(status=MovementStatus.CANCELLED)
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
