from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from src.domain.exceptions import InsufficientStockError, InvalidMovementError


@dataclass
class Stock:
    id: int
    product_id: int
    warehouse_id: int
    qty_physical: int
    qty_reserved_fbs: int
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def qty_available(self) -> int:
        return self.qty_physical - self.qty_reserved_fbs

    def ensure_reservable(self, qty: int) -> None:
        if self.qty_available < qty:
            raise InsufficientStockError(
                f"Недостаточно доступного остатка: доступно {self.qty_available}, запрошено {qty}."
            )

    def ensure_available(self, qty: int) -> None:
        self.ensure_reservable(qty)

    def ensure_consumable(self, qty: int) -> None:
        if self.qty_physical < qty:
            raise InsufficientStockError(
                f"Недостаточно физического остатка: {self.qty_physical}, запрошено {qty}."
            )

    def ensure_releasable(self, qty: int) -> None:
        if self.qty_reserved_fbs < qty:
            raise InsufficientStockError(
                f"Недостаточно зарезервированного остатка: {self.qty_reserved_fbs}, запрошено {qty}."
            )

    def receive(self, qty: int) -> Stock:
        if qty <= 0:
            raise InvalidMovementError(f"Receive qty must be positive: {qty}")
        self.qty_physical += qty
        self.updated_at = datetime.now(UTC)
        return self

    def consume(self, qty: int) -> Stock:
        self.ensure_consumable(qty)
        self.qty_physical -= qty
        self.updated_at = datetime.now(UTC)
        return self

    def reserve(self, qty: int) -> Stock:
        self.ensure_reservable(qty)
        self.qty_reserved_fbs += qty
        self.updated_at = datetime.now(UTC)
        return self

    def release_reservation(self, qty: int) -> Stock:
        self.ensure_releasable(qty)
        self.qty_reserved_fbs -= qty
        self.updated_at = datetime.now(UTC)
        return self
