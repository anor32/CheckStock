from __future__ import annotations

from dataclasses import dataclass, field

from src.domain.value_objects.stock_availability import WarehouseStockAvailability


@dataclass(frozen=True)
class InsufficientStockInfo:
    available: int
    requested: int
    other_warehouses: list[WarehouseStockAvailability] = field(default_factory=list)
    other_total_available: int = 0
    is_sufficient_in_total: bool = False
    candidate_warehouses: list[WarehouseStockAvailability] = field(default_factory=list)
    detail: str = ""

    @classmethod
    def build(
        cls,
        *,
        available: int,
        requested: int,
        other_warehouses: list[WarehouseStockAvailability],
    ) -> InsufficientStockInfo:
        warehouses = list(other_warehouses)
        other_total_available = sum(item.qty_available for item in warehouses)
        is_sufficient_in_total = other_total_available >= requested
        candidate_warehouses = [item for item in warehouses if item.qty_available > 0]
        detail = cls._build_detail(
            available=available,
            requested=requested,
            other_total_available=other_total_available,
            is_sufficient_in_total=is_sufficient_in_total,
            candidate_warehouses=candidate_warehouses,
        )
        return cls(
            available=available,
            requested=requested,
            other_warehouses=warehouses,
            other_total_available=other_total_available,
            is_sufficient_in_total=is_sufficient_in_total,
            candidate_warehouses=candidate_warehouses,
            detail=detail,
        )

    @classmethod
    def _build_detail(
        cls,
        *,
        available: int,
        requested: int,
        other_total_available: int,
        is_sufficient_in_total: bool,
        candidate_warehouses: list[WarehouseStockAvailability],
    ) -> str:
        base = (
            f"Недостаточно остатка на выбранном складе: доступно {available}, запрошено {requested}. "
            f"На других активных складах доступно суммарно {other_total_available}."
        )
        if is_sufficient_in_total:
            if candidate_warehouses:
                candidates = ", ".join(
                    f"{item.warehouse_name} (id={item.warehouse_id}): доступно {item.qty_available}"
                    for item in candidate_warehouses
                )
                return f"{base} Этого достаточно для операции. Склады-кандидаты: {candidates}."
            return f"{base} Этого достаточно для операции."
        return f"{base} Этого недостаточно для операции."

    def to_error_data(self) -> dict[str, object]:
        return {
            "available": self.available,
            "requested": self.requested,
            "other_warehouses": list(self.other_warehouses),
            "other_total_available": self.other_total_available,
            "is_sufficient_in_total": self.is_sufficient_in_total,
            "candidate_warehouses": list(self.candidate_warehouses),
            "detail": self.detail,
        }
