"""FBS reserve movement use case."""

from __future__ import annotations

from src.application.dtos import CreateFbsReserveMovementInput, CreateStockDTO
from src.domain.entities import Movement, Stock, Warehouse
from src.domain.exceptions import InsufficientStockError, StockNotFoundError
from src.domain.interfaces import IUnitOfWork
from src.domain.value_objects.insufficient_stock import InsufficientStockInfo


class FbsReserveMovementUseCase:
    def __init__(self, uow: IUnitOfWork) -> None:
        self.uow = uow

    async def execute(self, input_data: CreateFbsReserveMovementInput) -> Movement:
        existing = await self._get_existing_movement(input_data.idempotency_key)
        if existing is not None:
            return existing

        movement = await self.uow.movement_repo.add_movement(input_data.to_create_movement_dto())
        await self._ensure_entities(input_data.product_id, input_data.warehouse_id)
        stock = await self._get_or_create_stock(input_data.product_id, input_data.warehouse_id)
        await self._ensure_reservable(stock, input_data)
        stock.reserve(input_data.qty)
        await self.uow.stock_repo.update(stock)
        return movement

    async def _get_existing_movement(self, idempotency_key: str | None) -> Movement | None:
        if not idempotency_key:
            return None
        return await self.uow.movement_repo.get_by_idempotency_key(idempotency_key)

    async def _ensure_entities(self, product_id: int, warehouse_id: int) -> Warehouse:
        await self.uow.sku_repo.get_by_id(product_id)
        warehouse = await self.uow.warehouse_repo.get_by_id(warehouse_id)
        warehouse.ensure_active()
        return warehouse

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

    async def _ensure_reservable(
        self, stock: Stock, input_data: CreateFbsReserveMovementInput
    ) -> None:
        try:
            stock.ensure_reservable(input_data.qty)
        except InsufficientStockError as err:
            other_warehouses = await self.uow.stock_repo.list_other_warehouses_availability(
                input_data.product_id, input_data.warehouse_id
            )
            info = InsufficientStockInfo.build(
                available=stock.qty_available,
                requested=input_data.qty,
                other_warehouses=other_warehouses,
            )
            raise InsufficientStockError(info=info) from err
