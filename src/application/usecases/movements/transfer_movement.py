"""Transfer movement between warehouses use case."""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError

from src.application.dtos import CreateStockDTO, CreateTransferMovementInput
from src.domain.entities import Movement, Stock, Warehouse
from src.domain.exceptions import InsufficientStockError, StockNotFoundError
from src.domain.interfaces import IUnitOfWork
from src.domain.value_objects.insufficient_stock import InsufficientStockInfo


class TransferMovementUseCase:
    def __init__(self, uow: IUnitOfWork) -> None:
        self.uow = uow

    async def execute(self, input_data: CreateTransferMovementInput) -> Movement:
        existing = await self._get_existing_movement(input_data.idempotency_key)
        if existing is not None:
            return existing

        try:
            async with self.uow.begin_nested():
                movement = await self.uow.movement_repo.add_movement(
                    input_data.to_create_movement_dto()
                )
        except IntegrityError:
            existing = await self._get_existing_movement(input_data.idempotency_key)
            if existing is not None:
                return existing
            raise

        from_warehouse, _ = await self._ensure_transfer_entities(
            input_data.product_id, input_data.from_warehouse_id, input_data.to_warehouse_id
        )
        from_stock = await self._get_or_create_stock(
            input_data.product_id, input_data.from_warehouse_id
        )
        await self._ensure_reservable(from_stock, from_warehouse, input_data)
        from_stock.consume(input_data.qty)
        await self.uow.stock_repo.update(from_stock)
        return movement

    async def _get_existing_movement(self, idempotency_key: str | None) -> Movement | None:
        if not idempotency_key:
            return None
        return await self.uow.movement_repo.get_by_idempotency_key(idempotency_key)

    async def _ensure_transfer_entities(
        self, product_id: int, from_warehouse_id: int, to_warehouse_id: int
    ) -> tuple[Warehouse, Warehouse]:
        await self.uow.sku_repo.get_by_id(product_id)
        from_warehouse = await self.uow.warehouse_repo.get_by_id(from_warehouse_id)
        to_warehouse = await self.uow.warehouse_repo.get_by_id(to_warehouse_id)
        from_warehouse.ensure_active()
        to_warehouse.ensure_active()
        return from_warehouse, to_warehouse

    async def _get_or_create_stock(self, product_id: int, warehouse_id: int) -> Stock:
        try:
            _, stock, _ = await self.uow.stock_repo.get_by_product_and_warehouse_for_update(
                product_id, warehouse_id
            )
        except StockNotFoundError:
            return await self.uow.stock_repo.create(
                CreateStockDTO(product_id=product_id, warehouse_id=warehouse_id)
            )
        return stock

    async def _ensure_reservable(
        self, stock: Stock, warehouse: Warehouse, input_data: CreateTransferMovementInput
    ) -> None:
        try:
            stock.ensure_reservable(input_data.qty)
        except InsufficientStockError as err:
            other_warehouses = await self.uow.stock_repo.list_other_warehouses_availability(
                input_data.product_id, input_data.from_warehouse_id
            )
            info = InsufficientStockInfo.build(
                available=stock.qty_available,
                requested=input_data.qty,
                other_warehouses=other_warehouses,
            )
            raise InsufficientStockError(info=info) from err
