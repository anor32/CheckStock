from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dtos import CreateStockDTO, ListStocksDTO, StockListItemDTO
from src.domain.entities import Product, Stock, Warehouse, WarehouseStockAvailability
from src.domain.exceptions import StockNotFoundError
from src.domain.interfaces import IStockRepository
from src.infrastructure.models import ProductModel, StockModel, WarehouseModel


class SqlAlchemyStockRepository(IStockRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_product_and_warehouse(
        self, product_id: int, warehouse_id: int
    ) -> tuple[Product, Stock, Warehouse]:
        stmt = (
            select(ProductModel, StockModel, WarehouseModel)
            .join(StockModel, StockModel.product_id == ProductModel.id)
            .join(WarehouseModel, WarehouseModel.id == StockModel.warehouse_id)
            .where(ProductModel.id == product_id, WarehouseModel.id == warehouse_id)
        )
        row = (await self.session.execute(stmt)).first()
        if row is None:
            raise StockNotFoundError(
                f"Stock not found for product_id={product_id}, warehouse_id={warehouse_id}"
            )
        product_model, stock_model, warehouse_model = row.tuple()
        return product_model.to_entity(), stock_model.to_entity(), warehouse_model.to_entity()

    async def list_stocks(self, query: ListStocksDTO) -> tuple[list[StockListItemDTO], int]:
        filters = self._stock_filters(query)

        count_stmt = (
            select(func.count())
            .select_from(StockModel)
            .join(ProductModel, StockModel.product_id == ProductModel.id)
            .join(WarehouseModel, WarehouseModel.id == StockModel.warehouse_id)
        )
        if filters:
            count_stmt = count_stmt.where(*filters)
        total = int((await self.session.execute(count_stmt)).scalar_one())

        stmt = (
            select(ProductModel, StockModel, WarehouseModel)
            .join(StockModel, StockModel.product_id == ProductModel.id)
            .join(WarehouseModel, WarehouseModel.id == StockModel.warehouse_id)
        )
        if filters:
            stmt = stmt.where(*filters)
        stmt = (
            stmt.order_by(ProductModel.id, WarehouseModel.id)
            .offset((query.page - 1) * query.page_size)
            .limit(query.page_size)
        )
        rows = (await self.session.execute(stmt)).all()

        items = [
            StockListItemDTO.from_models(product_model, stock_model, warehouse_model)
            for product_model, stock_model, warehouse_model in (row.tuple() for row in rows)
        ]
        return items, total

    async def get_by_id(self, stock_id: int) -> Stock:
        stock_model = await self.session.get(StockModel, stock_id)
        if stock_model is None:
            raise StockNotFoundError(f"Stock not found: {stock_id}")
        return stock_model.to_entity()

    async def update(self, stock: Stock) -> Stock:
        stock_model = await self.session.get(StockModel, stock.id)
        if stock_model is None:
            raise StockNotFoundError(f"Stock not found: {stock.id}")
        stock_model.qty_physical = stock.qty_physical
        stock_model.qty_reserved_fbs = stock.qty_reserved_fbs
        await self.session.flush()
        await self.session.refresh(stock_model)
        return stock_model.to_entity()

    async def create(self, data: CreateStockDTO) -> Stock:
        stock_model = StockModel.from_create_dto(data)
        self.session.add(stock_model)
        await self.session.flush()
        await self.session.refresh(stock_model)
        return stock_model.to_entity()

    async def list_other_warehouses_availability(
        self, product_id: int, exclude_warehouse_id: int
    ) -> list[WarehouseStockAvailability]:
        stmt = (
            select(StockModel, WarehouseModel)
            .join(WarehouseModel, WarehouseModel.id == StockModel.warehouse_id)
            .where(
                StockModel.product_id == product_id,
                StockModel.warehouse_id != exclude_warehouse_id,
                WarehouseModel.is_deleted.is_(False),
            )
            .order_by((StockModel.qty_physical - StockModel.qty_reserved_fbs).desc())
        )
        rows = (await self.session.execute(stmt)).all()
        return [
            WarehouseStockAvailability.from_models(stock_model, warehouse_model)
            for stock_model, warehouse_model in rows
        ]

    def _stock_filters(self, query: ListStocksDTO) -> list[Any]:
        filters: list[Any] = []
        if query.sku:
            filters.append(ProductModel.sku == query.sku)
        if query.warehouse_id is not None:
            filters.append(WarehouseModel.id == query.warehouse_id)
        if not query.include_deleted_warehouses:
            filters.append(WarehouseModel.is_deleted.is_(False))
        return filters
