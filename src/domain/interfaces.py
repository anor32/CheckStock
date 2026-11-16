"""Domain interfaces for CheckStock dependencies (TASK_05)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Self

from src.application.dtos import (
    CreateMovementDTO,
    CreateProductDTO,
    CreateStockDTO,
    CreateWarehouseDTO,
    ListMovementsDTO,
    ListStocksDTO,
    StockListItemDTO,
)
from src.domain.entities import Movement, Product, Stock, Warehouse, WarehouseStockAvailability


class ISkuRepository(ABC):
    @abstractmethod
    async def get_by_id(self, product_id: int) -> Product: ...

    @abstractmethod
    async def get_by_sku(self, sku: str) -> Product: ...

    @abstractmethod
    async def add(self, data: CreateProductDTO) -> Product: ...

    @abstractmethod
    async def list_all(self) -> list[Product]: ...


class IWarehouseRepository(ABC):
    """Репозиторий складов."""

    @abstractmethod
    async def get_by_id(self, warehouse_id: int, include_deleted: bool = False) -> Warehouse: ...

    @abstractmethod
    async def create(self, data: CreateWarehouseDTO) -> Warehouse: ...

    @abstractmethod
    async def update(self, warehouse: Warehouse) -> Warehouse: ...

    @abstractmethod
    async def list_all(self, include_deleted: bool = True) -> list[Warehouse]: ...


class IStockRepository(ABC):
    """Репозиторий остатков."""

    @abstractmethod
    async def get_by_product_and_warehouse(
        self, product_id: int, warehouse_id: int
    ) -> tuple[Product, Stock, Warehouse]: ...

    @abstractmethod
    async def get_by_product_and_warehouse_for_update(
        self, product_id: int, warehouse_id: int
    ) -> tuple[Product, Stock, Warehouse]: ...

    @abstractmethod
    async def list_stocks(self, query: ListStocksDTO) -> tuple[list[StockListItemDTO], int]: ...

    @abstractmethod
    async def get_by_id(self, stock_id: int) -> Stock: ...

    @abstractmethod
    async def update(self, stock: Stock) -> Stock: ...

    @abstractmethod
    async def create(self, data: CreateStockDTO) -> Stock: ...

    @abstractmethod
    async def list_other_warehouses_availability(
        self, product_id: int, exclude_warehouse_id: int
    ) -> list[WarehouseStockAvailability]: ...


class IMovementRepository(ABC):
    """Репозиторий движений."""

    @abstractmethod
    async def add_movement(self, data: CreateMovementDTO) -> Movement: ...

    @abstractmethod
    async def save_movement(self, movement: Movement) -> Movement: ...

    @abstractmethod
    async def get_movement(self, movement_id: int) -> Movement: ...

    @abstractmethod
    async def get_by_idempotency_key(self, idempotency_key: str) -> Movement | None: ...

    @abstractmethod
    async def list_movements(self, query: ListMovementsDTO) -> tuple[list[Movement], int]: ...


class IUnitOfWork(ABC):
    sku_repo: ISkuRepository
    warehouse_repo: IWarehouseRepository
    stock_repo: IStockRepository
    movement_repo: IMovementRepository

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
