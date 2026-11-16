from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from src.domain.exceptions import EntityNotFoundError, InvalidMovementError
from src.domain.value_objects.movement import MovementStatus, MovementType


@dataclass
class Movement:
    id: int
    product_id: int
    type: MovementType
    qty: int
    from_warehouse_id: int | None = None
    to_warehouse_id: int | None = None
    status: MovementStatus = MovementStatus.PENDING
    idempotency_key: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.qty <= 0:
            raise InvalidMovementError(f"Movement qty must be positive: {self.qty}")
        if (
            self.type
            in (
                MovementType.TRANSFER_OUT,
                MovementType.FBO_OUT,
                MovementType.FBS_RESERVE,
                MovementType.FBS_SHIP,
                MovementType.FBS_CANCEL,
            )
            and self.from_warehouse_id is None
        ):
            raise InvalidMovementError(
                f"Movement type {self.type.value} requires from_warehouse_id"
            )
        if (
            self.type
            in (
                MovementType.INBOUND,
                MovementType.TRANSFER_IN,
                MovementType.FBO_RECEIVED,
            )
            and self.to_warehouse_id is None
        ):
            raise InvalidMovementError(f"Movement type {self.type.value} requires to_warehouse_id")

    def ensure_type(self, expected: MovementType) -> None:
        """Несоответствие типа трактуется как «движение не найдено» (404)."""
        if self.type != expected:
            raise EntityNotFoundError(f"Movement of type {expected.value} not found")

    def ensure_fbs_reserve_pending(self) -> None:
        if self.type != MovementType.FBS_RESERVE or self.status != MovementStatus.PENDING:
            raise InvalidMovementError(
                f"FBS reserve movement must be pending for this operation: "
                f"type={self.type.value}, status={self.status.value}"
            )

    def ensure_from_warehouse_id(self) -> int:
        if self.from_warehouse_id is None:
            raise EntityNotFoundError("Warehouse not found")
        return self.from_warehouse_id

    def ensure_to_warehouse_id(self) -> int:
        if self.to_warehouse_id is None:
            raise EntityNotFoundError("Destination warehouse not found")
        return self.to_warehouse_id

    def is_completed(self) -> bool:
        return self.status == MovementStatus.COMPLETED

    def is_cancelled(self) -> bool:
        return self.status == MovementStatus.CANCELLED

    def is_in_transit(self) -> bool:
        return self.status == MovementStatus.IN_TRANSIT

    def is_fbs_ship_in_transit(self) -> bool:
        """Идемпотентный no-op: FBS-отгрузка уже переведена в статус in_transit."""
        return self.type == MovementType.FBS_SHIP and self.status == MovementStatus.IN_TRANSIT

    def ship_fbs(self) -> Movement:
        self.type = MovementType.FBS_SHIP
        self.status = MovementStatus.IN_TRANSIT
        self.completed_at = None
        return self

    def complete(
        self,
        *,
        status: MovementStatus = MovementStatus.COMPLETED,
        completed_at: datetime | None = None,
        set_completed_at_now: bool = True,
    ) -> Movement:
        self.status = status
        if completed_at is not None:
            self.completed_at = completed_at
        elif set_completed_at_now:
            self.completed_at = datetime.now(UTC)
        else:
            self.completed_at = None
        return self
