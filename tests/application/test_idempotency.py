from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from src.application.dtos import FbsShipMovementInput
from src.application.usecases.movements.fbs_ship_movement import FbsShipMovementUseCase
from src.domain.entities import Movement, MovementStatus, MovementType, Product, Stock, Warehouse
from src.domain.exceptions import DuplicateIdempotencyKeyError


@pytest.mark.asyncio
async def test_fbs_ship_idempotency_does_not_double_deduct(mock_uow):
    stock = Stock(id=1, product_id=1, warehouse_id=1, qty_physical=10, qty_reserved_fbs=4)
    warehouse = Warehouse(id=1, name="Север")
    product = Product(id=1, sku="SKU-1", name="Товар")

    movement = Movement(
        id=10,
        product_id=1,
        type=MovementType.FBS_RESERVE,
        qty=2,
        from_warehouse_id=1,
        status=MovementStatus.PENDING,
        created_at=datetime.now(UTC),
    )

    mock_uow.movement_repo.get_movement = AsyncMock(return_value=movement)
    mock_uow.warehouse_repo.get_by_id = AsyncMock(return_value=warehouse)
    mock_uow.stock_repo.get_by_product_and_warehouse = AsyncMock(
        return_value=(product, stock, warehouse)
    )
    mock_uow.stock_repo.update = AsyncMock(side_effect=lambda obj: obj)
    mock_uow.movement_repo.save_movement = AsyncMock(side_effect=lambda obj: obj)

    use_case = FbsShipMovementUseCase(uow=mock_uow)
    input_data = FbsShipMovementInput(movement_id=10, idempotency_key="key-123")

    result1 = await use_case.execute(input_data)

    assert stock.qty_physical == 8
    assert stock.qty_reserved_fbs == 2
    assert result1.status == MovementStatus.IN_TRANSIT

    with pytest.raises(DuplicateIdempotencyKeyError):
        await use_case.execute(input_data)

    assert stock.qty_physical == 8, "Повторная отгрузка списала товар второй раз!"
    assert stock.qty_reserved_fbs == 2, "Повторная отгрузка списала резерв второй раз!"
