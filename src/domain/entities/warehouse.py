from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from src.domain.exceptions import WarehouseDeletedError


@dataclass(frozen=True)
class WarehouseStockAvailability:
    warehouse_id: int
    warehouse_name: str
    qty_available: int
    qty_physical: int
    qty_reserved_fbs: int


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
