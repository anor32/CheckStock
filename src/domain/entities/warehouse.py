from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from src.domain.exceptions import WarehouseDeletedError


@dataclass(frozen=True)
class WarehouseStockAvailability:
    warehouse_id: int
    warehouse_name: str
    qty_available: int
    qty_physical: int
    qty_reserved_fbs: int

    @classmethod
    def from_models(cls, stock: Any, warehouse: Any) -> WarehouseStockAvailability:
        qty_physical = stock.qty_physical
        qty_reserved_fbs = stock.qty_reserved_fbs
        qty_available = getattr(stock, "qty_available", qty_physical - qty_reserved_fbs)
        return cls(
            warehouse_id=warehouse.id,
            warehouse_name=warehouse.name,
            qty_available=qty_available,
            qty_physical=qty_physical,
            qty_reserved_fbs=qty_reserved_fbs,
        )


@dataclass
class Warehouse:
    id: int
    name: str
    is_deleted: bool = False
    deleted_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def ensure_active(self) -> None:
        if self.is_deleted:
            raise WarehouseDeletedError(f"Warehouse is deleted: {self.id}")

    def mark_deleted(self) -> None:
        """Soft delete: помечает склад удалённым, не удаляя запись физически."""
        self.is_deleted = True
        self.deleted_at = datetime.now(UTC)
