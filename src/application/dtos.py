"""Application DTOs (CQRS): Create (no id) / Update (with id) / Result (with id) / Query."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.application.pagination import Pagination
from src.domain.entities import Movement, MovementStatus, MovementType, Product, Stock, Warehouse


@dataclass(frozen=True)
class CreateProductDTO:
    sku: str
    name: str

    def __post_init__(self) -> None:
        if not self.sku or not self.sku.strip():
            raise ValueError("sku must not be empty")
        if not self.name or not self.name.strip():
            raise ValueError("name must not be empty")


@dataclass(frozen=True)
class CreateWarehouseDTO:
    name: str

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("name must not be empty")


@dataclass(frozen=True)
class CreateStockDTO:
    product_id: int
    warehouse_id: int
    qty_physical: int = 0
    qty_reserved_fbs: int = 0

    def __post_init__(self) -> None:
        if self.product_id <= 0:
            raise ValueError("product_id must be positive")
        if self.warehouse_id <= 0:
            raise ValueError("warehouse_id must be positive")
        if self.qty_physical < 0:
            raise ValueError("qty_physical must be non-negative")
        if self.qty_reserved_fbs < 0:
            raise ValueError("qty_reserved_fbs must be non-negative")


@dataclass(frozen=True)
class CreateMovementDTO:
    product_id: int
    type: MovementType
    qty: int
    from_warehouse_id: int | None = None
    to_warehouse_id: int | None = None
    status: MovementStatus = MovementStatus.PENDING
    idempotency_key: str | None = None
    completed_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.product_id <= 0:
            raise ValueError("product_id must be positive")
        if self.qty <= 0:
            raise ValueError("qty must be positive")


@dataclass(frozen=True)
class CreateInboundMovementInput:
    product_id: int
    warehouse_id: int
    qty: int
    idempotency_key: str | None = None

    def __post_init__(self) -> None:
        if self.product_id <= 0:
            raise ValueError("product_id must be positive")
        if self.warehouse_id <= 0:
            raise ValueError("warehouse_id must be positive")
        if self.qty <= 0:
            raise ValueError("qty must be positive")

    def to_create_movement_dto(self) -> CreateMovementDTO:
        return CreateMovementDTO(
            product_id=self.product_id,
            type=MovementType.INBOUND,
            qty=self.qty,
            to_warehouse_id=self.warehouse_id,
            status=MovementStatus.COMPLETED,
            idempotency_key=self.idempotency_key,
        )


@dataclass(frozen=True)
class CreateTransferMovementInput:
    product_id: int
    from_warehouse_id: int
    to_warehouse_id: int
    qty: int
    idempotency_key: str | None = None

    def __post_init__(self) -> None:
        if self.product_id <= 0:
            raise ValueError("product_id must be positive")
        if self.from_warehouse_id <= 0:
            raise ValueError("from_warehouse_id must be positive")
        if self.to_warehouse_id <= 0:
            raise ValueError("to_warehouse_id must be positive")
        if self.qty <= 0:
            raise ValueError("qty must be positive")

    def to_create_movement_dto(self) -> CreateMovementDTO:
        return CreateMovementDTO(
            product_id=self.product_id,
            type=MovementType.TRANSFER_OUT,
            qty=self.qty,
            from_warehouse_id=self.from_warehouse_id,
            to_warehouse_id=self.to_warehouse_id,
            status=MovementStatus.IN_TRANSIT,
            idempotency_key=self.idempotency_key,
        )


@dataclass(frozen=True)
class CreateFboOutMovementInput:
    product_id: int
    from_warehouse_id: int
    qty: int
    idempotency_key: str | None = None

    def __post_init__(self) -> None:
        if self.product_id <= 0:
            raise ValueError("product_id must be positive")
        if self.from_warehouse_id <= 0:
            raise ValueError("from_warehouse_id must be positive")
        if self.qty <= 0:
            raise ValueError("qty must be positive")

    def to_create_movement_dto(self) -> CreateMovementDTO:
        return CreateMovementDTO(
            product_id=self.product_id,
            type=MovementType.FBO_OUT,
            qty=self.qty,
            from_warehouse_id=self.from_warehouse_id,
            status=MovementStatus.IN_TRANSIT,
            idempotency_key=self.idempotency_key,
        )


@dataclass(frozen=True)
class CreateFbsReserveMovementInput:
    product_id: int
    warehouse_id: int
    qty: int
    idempotency_key: str | None = None

    def __post_init__(self) -> None:
        if self.product_id <= 0:
            raise ValueError("product_id must be positive")
        if self.warehouse_id <= 0:
            raise ValueError("warehouse_id must be positive")
        if self.qty <= 0:
            raise ValueError("qty must be positive")

    def to_create_movement_dto(self) -> CreateMovementDTO:
        return CreateMovementDTO(
            product_id=self.product_id,
            type=MovementType.FBS_RESERVE,
            qty=self.qty,
            from_warehouse_id=self.warehouse_id,
            status=MovementStatus.PENDING,
            idempotency_key=self.idempotency_key,
        )


# ---------- Commands (actions on existing movements) ----------
@dataclass(frozen=True)
class ReceiveMovementInput:
    movement_id: int
    idempotency_key: str | None = None

    def __post_init__(self) -> None:
        if self.movement_id <= 0:
            raise ValueError("movement_id must be positive")


@dataclass(frozen=True)
class FboReceiveMovementInput:
    movement_id: int
    idempotency_key: str | None = None

    def __post_init__(self) -> None:
        if self.movement_id <= 0:
            raise ValueError("movement_id must be positive")


@dataclass(frozen=True)
class FbsShipMovementInput:
    movement_id: int
    idempotency_key: str | None = None

    def __post_init__(self) -> None:
        if self.movement_id <= 0:
            raise ValueError("movement_id must be positive")


@dataclass(frozen=True)
class FbsCancelMovementInput:
    movement_id: int
    idempotency_key: str | None = None

    def __post_init__(self) -> None:
        if self.movement_id <= 0:
            raise ValueError("movement_id must be positive")


# ---------- Commands (Update) ----------
@dataclass(frozen=True)
class UpdateWarehouseInput:
    warehouse_id: int
    name: str

    def __post_init__(self) -> None:
        if self.warehouse_id <= 0:
            raise ValueError("warehouse_id must be positive")
        if not self.name or not self.name.strip():
            raise ValueError("name must not be empty")


# (Result DTOs removed: use cases return Domain entities directly)


@dataclass(frozen=True)
class StockListItemDTO:
    """Read model for stock list/detail views."""

    product_id: int
    sku: str
    product_name: str
    warehouse_id: int
    warehouse_name: str
    warehouse_is_deleted: bool
    qty_physical: int
    qty_reserved_fbs: int
    qty_available: int

    @classmethod
    def from_entities(
        cls, product: Product, stock: Stock, warehouse: Warehouse
    ) -> StockListItemDTO:
        return cls(
            product_id=product.id,
            sku=product.sku,
            product_name=product.name,
            warehouse_id=warehouse.id,
            warehouse_name=warehouse.name,
            warehouse_is_deleted=warehouse.is_deleted,
            qty_physical=stock.qty_physical,
            qty_reserved_fbs=stock.qty_reserved_fbs,
            qty_available=stock.qty_available,
        )

    @classmethod
    def from_models(cls, product: Any, stock: Any, warehouse: Any) -> StockListItemDTO:
        qty_physical = stock.qty_physical
        qty_reserved_fbs = stock.qty_reserved_fbs
        qty_available = getattr(stock, "qty_available", qty_physical - qty_reserved_fbs)
        return cls(
            product_id=product.id,
            sku=product.sku,
            product_name=product.name,
            warehouse_id=warehouse.id,
            warehouse_name=warehouse.name,
            warehouse_is_deleted=warehouse.is_deleted,
            qty_physical=qty_physical,
            qty_reserved_fbs=qty_reserved_fbs,
            qty_available=qty_available,
        )


@dataclass(frozen=True)
class WarehouseListItemDTO:
    """Read model for warehouse list view."""

    id: int
    name: str
    is_deleted: bool

    @classmethod
    def from_entity(cls, warehouse: Warehouse) -> WarehouseListItemDTO:
        return cls(id=warehouse.id, name=warehouse.name, is_deleted=warehouse.is_deleted)


# ---------- Queries (List) ----------
@dataclass(frozen=True)
class ListMovementsQuery:
    """Запрос на вывод истории операций."""

    pagination: Pagination = field(default_factory=Pagination)
    product_id: int | None = None
    movement_type: MovementType | None = None
    status: MovementStatus | None = None
    warehouse_id: int | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None


@dataclass(frozen=True)
class ListStocksQuery:
    """Запрос на вывод списка остатков."""

    pagination: Pagination = field(default_factory=Pagination)
    sku: str | None = None
    warehouse_id: int | None = None
    include_deleted_warehouses: bool = True


@dataclass(frozen=True)
class ListWarehousesQuery:
    """Запрос на вывод списка складов."""

    include_deleted: bool = False


# ---------- Paginated Results ----------
@dataclass(frozen=True)
class PaginatedMovementsDTO:
    items: list[Movement]
    total: int
    page: int
    page_size: int


@dataclass(frozen=True)
class PaginatedStocksDTO:
    items: list[StockListItemDTO]
    total: int
    page: int
    page_size: int


# ---------- Compatibility aliases (to be removed after full migration) ----------
CreateProductInput = CreateProductDTO
CreateWarehouseInput = CreateWarehouseDTO
InboundMovementInput = CreateInboundMovementInput
TransferMovementInput = CreateTransferMovementInput
FboOutMovementInput = CreateFboOutMovementInput
FbsReserveMovementInput = CreateFbsReserveMovementInput
ListMovementsDTO = ListMovementsQuery
ListStocksDTO = ListStocksQuery
ListWarehousesDTO = ListWarehousesQuery
