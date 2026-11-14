"""Seed fixtures with test data from the CheckStock spec."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from sqlalchemy import select

from src.domain.entities import MovementStatus, MovementType
from src.infrastructure.db import async_session_factory
from src.infrastructure.models import MovementModel, ProductModel, StockModel, WarehouseModel

FIXTURE_IDEMPOTENCY_PREFIX = "spec:"


async def load_fixtures() -> dict[str, int]:
    """Load test fixtures into the database idempotently.

    Test data (1 магазин, 2 ФФ: Север, Юг), количества после тестового прихода:
    - SKU-101 Органайзер: Север 10, Юг 6
    - SKU-102 Контейнер:  Север 5,  Юг 0
    - SKU-103 Корзина:    Север 0,  Юг 4
    """
    inserted = {"products": 0, "warehouses": 0, "stocks": 0, "movements": 0}

    async with async_session_factory() as session, session.begin():
        existing = await session.execute(
            select(ProductModel.id).where(ProductModel.sku == "SKU-101")
        )
        if existing.scalar_one_or_none() is not None:
            return inserted

        now = datetime.now(UTC)

        wh_north = WarehouseModel(name="Север")
        wh_south = WarehouseModel(name="Юг")
        session.add_all([wh_north, wh_south])
        await session.flush()
        inserted["warehouses"] = 2

        p1 = ProductModel(sku="SKU-101", name="Органайзер")
        p2 = ProductModel(sku="SKU-102", name="Контейнер")
        p3 = ProductModel(sku="SKU-103", name="Корзина")
        session.add_all([p1, p2, p3])
        await session.flush()
        inserted["products"] = 3

        stocks_data = [
            (p1, wh_north, 10),
            (p1, wh_south, 6),
            (p2, wh_north, 5),
            (p2, wh_south, 0),
            (p3, wh_north, 0),
            (p3, wh_south, 4),
        ]
        stocks: list[StockModel] = []
        movements: list[MovementModel] = []
        for product, warehouse, qty in stocks_data:
            stocks.append(
                StockModel(
                    product_id=product.id,
                    warehouse_id=warehouse.id,
                    qty_physical=qty,
                    qty_reserved_fbs=0,
                )
            )
            if qty > 0:
                movements.append(
                    MovementModel(
                        product_id=product.id,
                        type=MovementType.INBOUND.value,
                        qty=qty,
                        from_warehouse_id=None,
                        to_warehouse_id=warehouse.id,
                        status=MovementStatus.COMPLETED.value,
                        idempotency_key=f"{FIXTURE_IDEMPOTENCY_PREFIX}inbound-{product.sku}-{warehouse.name}",
                        created_at=now,
                        completed_at=now,
                    )
                )

        session.add_all(stocks)
        await session.flush()
        inserted["stocks"] = len(stocks)

        session.add_all(movements)
        await session.flush()
        inserted["movements"] = len(movements)

    return inserted


def main() -> None:
    result = asyncio.run(load_fixtures())
    if sum(result.values()) == 0:
        print("Fixtures: already present, nothing inserted.")
    else:
        print(
            "Fixtures loaded: " + ", ".join(f"{table}={count}" for table, count in result.items())
        )


if __name__ == "__main__":
    main()
