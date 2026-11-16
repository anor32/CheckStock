from __future__ import annotations

from dataclasses import dataclass
from typing import Any


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
