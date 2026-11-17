"""Pydantic schemas for API."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from src.domain.entities import MovementStatus, MovementType, WarehouseStockAvailability
from src.domain.value_objects.insufficient_stock import InsufficientStockInfo


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sku: str
    name: str


class ProductCreateRequest(BaseModel):
    sku: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)


class WarehouseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    is_deleted: bool


class StockItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: int
    sku: str
    product_name: str
    warehouse_id: int
    warehouse_name: str
    warehouse_is_deleted: bool
    qty_physical: int
    qty_reserved_fbs: int
    qty_available: int


class PaginatedStocksResponse(BaseModel):
    items: list[StockItemResponse]
    total: int
    page: int
    page_size: int


class MovementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    type: MovementType
    qty: int = Field(..., gt=0)
    from_warehouse_id: int | None
    to_warehouse_id: int | None
    status: MovementStatus
    idempotency_key: str | None
    created_at: datetime
    completed_at: datetime | None


class PaginatedMovementsResponse(BaseModel):
    items: list[MovementResponse]
    total: int
    page: int
    page_size: int


class WarehouseCreateRequest(BaseModel):
    name: str = Field(..., min_length=1)


class WarehouseUpdateRequest(BaseModel):
    name: str = Field(..., min_length=1)


class InboundMovementRequest(BaseModel):
    product_id: int = Field(..., gt=0)
    warehouse_id: int = Field(..., gt=0)
    qty: int = Field(..., gt=0)
    idempotency_key: str | None = Field(default=None, min_length=1)


class TransferMovementRequest(BaseModel):
    product_id: int = Field(..., gt=0)
    from_warehouse_id: int = Field(..., gt=0)
    to_warehouse_id: int = Field(..., gt=0)
    qty: int = Field(..., gt=0)
    idempotency_key: str | None = Field(default=None, min_length=1)


class ReceiveMovementRequest(BaseModel):
    idempotency_key: str | None = Field(default=None, min_length=1)


class FboOutMovementRequest(BaseModel):
    product_id: int = Field(..., gt=0)
    from_warehouse_id: int = Field(..., gt=0)
    qty: int = Field(..., gt=0)
    idempotency_key: str | None = Field(default=None, min_length=1)


class FboReceiveMovementRequest(BaseModel):
    idempotency_key: str | None = Field(default=None, min_length=1)


class FbsReserveMovementRequest(BaseModel):
    product_id: int = Field(..., gt=0)
    warehouse_id: int = Field(..., gt=0)
    qty: int = Field(..., gt=0)
    idempotency_key: str | None = Field(default=None, min_length=1)


class FbsShipMovementRequest(BaseModel):
    idempotency_key: str | None = Field(default=None, min_length=1)


class FbsCancelMovementRequest(BaseModel):
    idempotency_key: str | None = Field(default=None, min_length=1)


class ListMovementsRequest(BaseModel):
    """Схема запроса списка движений — один объект вместо разрозненных query-параметров."""

    model_config = ConfigDict(populate_by_name=True)

    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    product_id: int | None = None
    movement_type: MovementType | None = Field(
        default=None,
        validation_alias=AliasChoices("movement_type", "type"),
    )
    status: MovementStatus | None = None
    warehouse_id: int | None = None
    date_from: str | None = None
    date_to: str | None = None


class ListStocksRequest(BaseModel):
    """Схема запроса списка остатков."""

    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    sku: str | None = None
    warehouse_id: int | None = None
    include_deleted_warehouses: bool = True


class ListWarehousesRequest(BaseModel):
    """Схема запроса списка складов."""

    include_deleted: bool = False


class OtherWarehouseAvailabilityResponse(BaseModel):
    warehouse_id: int
    warehouse_name: str
    qty_available: int
    qty_physical: int
    qty_reserved_fbs: int


class ErrorResponse(BaseModel):
    detail: str
    available: int
    requested: int
    other_warehouses: list[OtherWarehouseAvailabilityResponse] | None = None
    other_total_available: int | None = None
    is_sufficient_in_total: bool | None = None

    @staticmethod
    def _serialize_other_warehouses(
        other_warehouses: list[Any] | None,
    ) -> list[OtherWarehouseAvailabilityResponse]:
        if not other_warehouses:
            return []
        result: list[OtherWarehouseAvailabilityResponse] = []
        for item in other_warehouses:
            if isinstance(item, WarehouseStockAvailability):
                result.append(
                    OtherWarehouseAvailabilityResponse(
                        warehouse_id=item.warehouse_id,
                        warehouse_name=item.warehouse_name,
                        qty_available=item.qty_available,
                        qty_physical=item.qty_physical,
                        qty_reserved_fbs=item.qty_reserved_fbs,
                    )
                )
            elif isinstance(item, dict):
                result.append(
                    OtherWarehouseAvailabilityResponse(
                        warehouse_id=item.get("warehouse_id", 0),
                        warehouse_name=item.get("warehouse_name", ""),
                        qty_available=item.get("qty_available", 0),
                        qty_physical=item.get("qty_physical", 0),
                        qty_reserved_fbs=item.get("qty_reserved_fbs", 0),
                    )
                )
            else:
                result.append(
                    OtherWarehouseAvailabilityResponse(
                        warehouse_id=getattr(item, "warehouse_id", 0),
                        warehouse_name=getattr(item, "warehouse_name", ""),
                        qty_available=getattr(item, "qty_available", 0),
                        qty_physical=getattr(item, "qty_physical", 0),
                        qty_reserved_fbs=getattr(item, "qty_reserved_fbs", 0),
                    )
                )
        return result

    @classmethod
    def build_detail(cls, data: dict[str, Any]) -> str:
        available = int(data.get("available", data.get("selected_qty", 0)))
        requested = int(data.get("requested", data.get("requested_qty", 0)))
        other_warehouses = cls._serialize_other_warehouses(data.get("other_warehouses"))
        other_total_available = data.get("other_total_available")
        if other_total_available is None:
            other_total_available = sum(item.qty_available for item in other_warehouses)
        else:
            other_total_available = int(other_total_available)
        is_sufficient_in_total = data.get("is_sufficient_in_total")
        if is_sufficient_in_total is None:
            is_sufficient_in_total = other_total_available >= requested
        else:
            is_sufficient_in_total = bool(is_sufficient_in_total)

        base = (
            f"Недостаточно остатка на выбранном складе: доступно {available}, запрошено {requested}. "
            f"На других активных складах доступно суммарно {other_total_available}."
        )
        if is_sufficient_in_total:
            if other_warehouses:
                candidates = ", ".join(
                    f"{item.warehouse_name} (id={item.warehouse_id}): доступно {item.qty_available}"
                    for item in other_warehouses
                    if item.qty_available > 0
                )
                if candidates:
                    return f"{base} Этого достаточно для операции. Склады-кандидаты: {candidates}."
            return f"{base} Этого достаточно для операции."
        return f"{base} Этого недостаточно для операции."

    @classmethod
    def from_error_data(cls, data: dict[str, Any] | InsufficientStockInfo | None) -> ErrorResponse:
        if isinstance(data, InsufficientStockInfo):
            other_warehouses = cls._serialize_other_warehouses(list(data.other_warehouses))
            return cls(
                detail=data.detail or cls.build_detail(data.to_error_data()),
                available=data.available,
                requested=data.requested,
                other_warehouses=other_warehouses or None,
                other_total_available=data.other_total_available,
                is_sufficient_in_total=data.is_sufficient_in_total,
            )

        payload = data or {}
        available = int(payload.get("available", payload.get("selected_qty", 0)))
        requested = int(payload.get("requested", payload.get("requested_qty", 0)))
        other_warehouses = cls._serialize_other_warehouses(payload.get("other_warehouses"))
        detail = str(payload.get("detail") or "")
        if not detail:
            detail = cls.build_detail(payload) if payload else "Недостаточно остатка для операции."

        other_total_available = payload.get("other_total_available")
        if other_total_available is None and payload:
            other_total_available = sum(item.qty_available for item in other_warehouses)
        if other_total_available is not None:
            other_total_available = int(other_total_available)

        is_sufficient_in_total = payload.get("is_sufficient_in_total")
        if is_sufficient_in_total is None and payload:
            is_sufficient_in_total = int(other_total_available or 0) >= requested
        if is_sufficient_in_total is not None:
            is_sufficient_in_total = bool(is_sufficient_in_total)

        return cls(
            detail=detail,
            available=available,
            requested=requested,
            other_warehouses=other_warehouses or None,
            other_total_available=other_total_available,
            is_sufficient_in_total=is_sufficient_in_total,
        )
