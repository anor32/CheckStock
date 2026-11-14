"""Domain interfaces for CheckStock dependencies (TASK_05)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Self

from src.application.dtos import ListMovementsQuery
from src.domain.entities import Movement, Product, Stock, Warehouse, WarehouseStockAvailability


class ISkuRepository(ABC):
    @abstractmethod
    async def get_by_id(self, product_id: int) -> Product: ...

    @abstractmethod
    async def get_by_sku(self, sku: str) -> Product: ...

    @abstractmethod
    async def add(self, product: Product) -> Product: ...

    @abstractmethod
    async def list_all(self) -> list[Product]: ...


class IWarehouseRepository(ABC):
    """Репозиторий складов."""

    @abstractmethod
    async def get_by_id(self, warehouse_id: int, include_deleted: bool = False) -> Warehouse: ...

    @abstractmethod
    async def add(self, warehouse: Warehouse) -> Warehouse: ...

    @abstractmethod
    async def save(self, warehouse: Warehouse) -> Warehouse: ...

    @abstractmethod
    async def list_all(self, include_deleted: bool = True) -> list[Warehouse]: ...


class IStockRepository(ABC):
    """Репозиторий остатков."""

    @abstractmethod
    async def get_by_product_and_warehouse(
        self, product_id: int, warehouse_id: int
    ) -> tuple[Product, Stock, Warehouse]: ...

    @abstractmethod
    async def list_stocks(
        self,
        page: int,
        page_size: int,
        sku: str | None = None,
        warehouse_id: int | None = None,
        include_deleted_warehouses: bool = True,
    ) -> tuple[list[tuple[Product, Stock, Warehouse]], int]: ...

    @abstractmethod
    async def get_or_create_for_product_warehouse(
        self, product_id: int, warehouse_id: int
    ) -> tuple[Product, Stock, Warehouse]: ...

    @abstractmethod
    async def get_by_id(self, stock_id: int) -> Stock: ...

    @abstractmethod
    async def save(self, stock: Stock) -> Stock: ...

    @abstractmethod
    async def add(self, stock: Stock) -> Stock: ...

    @abstractmethod
    async def list_other_warehouses_availability(
        self, product_id: int, exclude_warehouse_id: int
    ) -> list[WarehouseStockAvailability]: ...


class IOrderRepository(ABC):
    """Репозиторий заказов/движений."""

    @abstractmethod
    async def add_movement(self, movement: Movement) -> Movement: ...

    @abstractmethod
    async def save_movement(self, movement: Movement) -> Movement: ...

    @abstractmethod
    async def get_movement(self, movement_id: int) -> Movement: ...

    @abstractmethod
    async def list_movements(self, query: ListMovementsQuery) -> tuple[list[Movement], int]: ...


class IUnitOfWork(ABC):
    sku_repo: ISkuRepository
    warehouse_repo: IWarehouseRepository
    stock_repo: IStockRepository
    order_repo: IOrderRepository

    @abstractmethod
    async def __aenter__(self) -> Self: ...

    @abstractmethod
    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None: ...

    @abstractmethod
    async def commit(self) -> None: ...

    @abstractmethod
    async def rollback(self) -> None: ...


# Backward-compatible aliases
IUoW = IUnitOfWork
IRepository = ISkuRepository
IProductRepository = ISkuRepository
