"""FBS ship movement use case."""

from __future__ import annotations

from src.application.dtos import CreateStockDTO, FbsShipMovementInput
from src.domain.entities import Movement, MovementStatus, MovementType, Stock, Warehouse
from src.domain.exceptions import (
    DuplicateIdempotencyKeyError,
    InsufficientStockError,
    StockNotFoundError,
)
from src.domain.interfaces import IUnitOfWork


class FbsShipMovementUseCase:
    def __init__(self, uow: IUnitOfWork) -> None:
        self.uow = uow

    async def execute(self, input_data: FbsShipMovementInput) -> Movement:
        movement = await self.uow.movement_repo.get_movement(input_data.movement_id)
        if movement.is_fbs_ship_in_transit():
            if (
                input_data.idempotency_key is not None
                and movement.idempotency_key == input_data.idempotency_key
            ):
                raise DuplicateIdempotencyKeyError(
                    f"Duplicate idempotency key: {input_data.idempotency_key}"
                )
            return movement

        movement.ensure_type(MovementType.FBS_RESERVE)
        from_warehouse_id = movement.ensure_from_warehouse_id()
        warehouse = await self._get_active_warehouse(from_warehouse_id)
        stock = await self._get_or_create_stock(movement.product_id, from_warehouse_id)

        await self._ensure_consumable(stock, movement, warehouse)
        await self._ensure_releasable(stock, movement, warehouse)
        stock.consume(movement.qty)
        stock.release_reservation(movement.qty)
        await self.uow.stock_repo.update(stock)

        movement.complete(
            status=MovementStatus.IN_TRANSIT,
            idempotency_key=input_data.idempotency_key,
            set_completed_at_now=False,
        )
        return await self.uow.movement_repo.save_movement(movement)

    async def _get_active_warehouse(self, warehouse_id: int) -> Warehouse:
        warehouse = await self.uow.warehouse_repo.get_by_id(warehouse_id)
        warehouse.ensure_active()
        return warehouse

    async def _get_or_create_stock(self, product_id: int, warehouse_id: int) -> Stock:
        try:
            _, stock, _ = await self.uow.stock_repo.get_by_product_and_warehouse(
                product_id, warehouse_id
            )
        except StockNotFoundError:
            return await self.uow.stock_repo.create(
                CreateStockDTO(product_id=product_id, warehouse_id=warehouse_id)
            )
        else:
            return stock

    async def _ensure_consumable(
        self, stock: Stock, movement: Movement, warehouse: Warehouse
    ) -> None:
        try:
            stock.ensure_consumable(movement.qty)
        except InsufficientStockError as err:
            other_warehouses = await self.uow.stock_repo.list_other_warehouses_availability(
                movement.product_id, warehouse.id
            )
            raise InsufficientStockError(
                message="Недостаточно остатка для операции.",
                data={
                    "available": stock.qty_physical,
                    "requested": movement.qty,
                    "other_warehouses": other_warehouses,
                },
            ) from err

    async def _ensure_releasable(
        self, stock: Stock, movement: Movement, warehouse: Warehouse
    ) -> None:
        try:
            stock.ensure_releasable(movement.qty)
        except InsufficientStockError as err:
            other_warehouses = await self.uow.stock_repo.list_other_warehouses_availability(
                movement.product_id, warehouse.id
            )
            raise InsufficientStockError(
                message="Недостаточно остатка для операции.",
                data={
                    "available": stock.qty_reserved_fbs,
                    "requested": movement.qty,
                    "other_warehouses": other_warehouses,
                },
            ) from err
