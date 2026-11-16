from __future__ import annotations

from datetime import UTC, datetime

import pytest

from src.api.schemas import ErrorResponse
from src.application.dtos import FbsShipMovementInput
from src.application.usecases.movements.fbo_receive_movement import FboReceiveMovementUseCase
from src.application.usecases.movements.fbs_cancel_movement import FbsCancelMovementUseCase
from src.application.usecases.movements.fbs_reserve_movement import FbsReserveMovementUseCase
from src.application.usecases.movements.fbs_ship_movement import FbsShipMovementUseCase
from src.domain.entities import Movement, MovementStatus, MovementType, Stock
from src.domain.exceptions import DuplicateIdempotencyKeyError, InsufficientStockError


@pytest.mark.asyncio
async def test_fbo_receive_returns_existing_for_idempotent_request(
    mock_uow, fbo_receive_completed_movement, fbo_receive_input
) -> None:
    mock_uow.movement_repo.get_movement.return_value = fbo_receive_completed_movement
    use_case = FboReceiveMovementUseCase(uow=mock_uow)

    result = await use_case.execute(fbo_receive_input)

    assert result.id == fbo_receive_completed_movement.id
    assert result.status == MovementStatus.COMPLETED


@pytest.mark.asyncio
async def test_fbo_receive_completes_in_transit_movement(
    mock_uow, fbo_receive_in_transit_movement, warehouse, fbo_receive_input_no_key
) -> None:
    mock_uow.movement_repo.get_movement.return_value = fbo_receive_in_transit_movement
    mock_uow.warehouse_repo.get_by_id.return_value = warehouse
    use_case = FboReceiveMovementUseCase(uow=mock_uow)

    result = await use_case.execute(fbo_receive_input_no_key)

    assert result.status == MovementStatus.COMPLETED
    mock_uow.movement_repo.save_movement.assert_awaited_once()


@pytest.mark.asyncio
async def test_fbo_receive_is_noop_when_already_completed(
    mock_uow, fbo_receive_completed_movement, fbo_receive_input_no_key
) -> None:
    mock_uow.movement_repo.get_movement.return_value = fbo_receive_completed_movement
    use_case = FboReceiveMovementUseCase(uow=mock_uow)

    result = await use_case.execute(fbo_receive_input_no_key)

    assert result.status == MovementStatus.COMPLETED
    mock_uow.movement_repo.save_movement.assert_not_called()


@pytest.mark.asyncio
async def test_fbs_reserve_returns_existing_for_idempotent_request(
    mock_uow, fbs_reserve_existing_movement, fbs_reserve_input
) -> None:
    mock_uow.movement_repo.get_by_idempotency_key.return_value = fbs_reserve_existing_movement
    use_case = FbsReserveMovementUseCase(uow=mock_uow)

    result = await use_case.execute(fbs_reserve_input)

    assert result.id == fbs_reserve_existing_movement.id
    mock_uow.movement_repo.get_by_idempotency_key.assert_awaited_once_with(
        fbs_reserve_input.idempotency_key
    )
    mock_uow.movement_repo.add_movement.assert_not_called()
    mock_uow.sku_repo.get_by_id.assert_not_called()


@pytest.mark.asyncio
async def test_fbs_reserve_raises_insufficient_stock_when_not_enough_available(
    mock_uow, product, warehouse, stock_low_available, fbs_reserve_input_no_key, movement_from_dto
) -> None:
    mock_uow.sku_repo.get_by_id.return_value = product
    mock_uow.warehouse_repo.get_by_id.return_value = warehouse
    mock_uow.stock_repo.get_by_product_and_warehouse.return_value = (
        product,
        stock_low_available,
        warehouse,
    )
    mock_uow.movement_repo.add_movement.side_effect = movement_from_dto
    use_case = FbsReserveMovementUseCase(uow=mock_uow)

    with pytest.raises(InsufficientStockError) as exc:
        await use_case.execute(fbs_reserve_input_no_key)

    assert exc.value.data is not None
    assert exc.value.data["available"] == stock_low_available.qty_available
    assert exc.value.data["requested"] == fbs_reserve_input_no_key.qty


@pytest.mark.asyncio
async def test_fbs_reserve_increases_reserved_and_creates_pending_movement(
    mock_uow,
    product,
    warehouse,
    stock,
    fbs_reserve_saved_movement,
    fbs_reserve_input_new,
) -> None:
    mock_uow.sku_repo.get_by_id.return_value = product
    mock_uow.warehouse_repo.get_by_id.return_value = warehouse
    mock_uow.stock_repo.get_by_product_and_warehouse.return_value = (product, stock, warehouse)
    mock_uow.movement_repo.add_movement.return_value = fbs_reserve_saved_movement
    use_case = FbsReserveMovementUseCase(uow=mock_uow)

    result = await use_case.execute(fbs_reserve_input_new)

    assert stock.qty_reserved_fbs == 3
    assert result.status == MovementStatus.PENDING
    mock_uow.movement_repo.get_by_idempotency_key.assert_awaited_once_with(
        fbs_reserve_input_new.idempotency_key
    )
    mock_uow.stock_repo.update.assert_awaited_once_with(stock)


@pytest.mark.asyncio
async def test_fbs_ship_raises_duplicate_idempotency_key_when_already_in_transit(
    mock_uow, fbs_ship_in_transit_movement
) -> None:
    fbs_ship_in_transit_movement.idempotency_key = "ship-key-1"
    mock_uow.movement_repo.get_movement.return_value = fbs_ship_in_transit_movement
    use_case = FbsShipMovementUseCase(uow=mock_uow)

    with pytest.raises(DuplicateIdempotencyKeyError):
        await use_case.execute(FbsShipMovementInput(movement_id=70, idempotency_key="ship-key-1"))

    mock_uow.movement_repo.save_movement.assert_not_called()


@pytest.mark.asyncio
async def test_fbs_ship_updates_stock_and_marks_in_transit_to_customer(
    mock_uow,
    fbs_reserve_pending_movement,
    product,
    warehouse,
    stock_for_ship,
    fbs_ship_input,
) -> None:
    mock_uow.movement_repo.get_movement.return_value = fbs_reserve_pending_movement
    mock_uow.warehouse_repo.get_by_id.return_value = warehouse
    mock_uow.stock_repo.get_by_product_and_warehouse.return_value = (
        product,
        stock_for_ship,
        warehouse,
    )
    use_case = FbsShipMovementUseCase(uow=mock_uow)

    result = await use_case.execute(fbs_ship_input)

    assert stock_for_ship.qty_physical == 3
    assert stock_for_ship.qty_reserved_fbs == 0
    assert result.status == MovementStatus.IN_TRANSIT
    assert result.type == MovementType.FBS_SHIP
    assert result.completed_at is None
    mock_uow.stock_repo.update.assert_awaited_once_with(stock_for_ship)
    mock_uow.movement_repo.save_movement.assert_awaited_once()


@pytest.mark.asyncio
async def test_fbs_cancel_is_noop_when_already_cancelled(
    mock_uow, fbs_cancelled_movement, fbs_cancel_input
) -> None:
    mock_uow.movement_repo.get_movement.return_value = fbs_cancelled_movement
    use_case = FbsCancelMovementUseCase(uow=mock_uow)

    result = await use_case.execute(fbs_cancel_input)

    assert result.status == MovementStatus.CANCELLED
    mock_uow.movement_repo.save_movement.assert_not_called()


@pytest.mark.asyncio
async def test_fbs_cancel_releases_reservation_and_marks_cancelled(
    mock_uow,
    fbs_cancel_pending_movement,
    product,
    warehouse,
    stock_for_ship,
    fbs_cancel_input,
) -> None:
    mock_uow.movement_repo.get_movement.return_value = fbs_cancel_pending_movement
    mock_uow.warehouse_repo.get_by_id.return_value = warehouse
    mock_uow.stock_repo.get_by_product_and_warehouse.return_value = (
        product,
        stock_for_ship,
        warehouse,
    )
    use_case = FbsCancelMovementUseCase(uow=mock_uow)

    result = await use_case.execute(fbs_cancel_input)

    assert stock_for_ship.qty_reserved_fbs == 0
    assert result.status == MovementStatus.CANCELLED
    mock_uow.stock_repo.update.assert_awaited_once_with(stock_for_ship)
    mock_uow.movement_repo.save_movement.assert_awaited_once()


@pytest.mark.asyncio
async def test_fbs_reserve_raises_detailed_error_when_enough_on_other_warehouses(
    mock_uow,
    product,
    warehouse,
    stock_low_available,
    fbs_reserve_input_no_key,
    movement_from_dto,
    other_warehouse_availability_enough,
) -> None:
    mock_uow.sku_repo.get_by_id.return_value = product
    mock_uow.warehouse_repo.get_by_id.return_value = warehouse
    mock_uow.stock_repo.get_by_product_and_warehouse.return_value = (
        product,
        stock_low_available,
        warehouse,
    )
    mock_uow.stock_repo.list_other_warehouses_availability.return_value = [
        other_warehouse_availability_enough
    ]
    mock_uow.movement_repo.add_movement.side_effect = movement_from_dto
    use_case = FbsReserveMovementUseCase(uow=mock_uow)

    with pytest.raises(InsufficientStockError) as exc:
        await use_case.execute(fbs_reserve_input_no_key)

    data = exc.value.data
    info = exc.value.info
    assert data is not None
    assert info is not None
    assert data["available"] == stock_low_available.qty_available
    assert data["requested"] == fbs_reserve_input_no_key.qty
    assert data["other_warehouses"] == [other_warehouse_availability_enough]
    assert info.other_total_available == 5
    assert info.is_sufficient_in_total is True

    response = ErrorResponse.from_error_data(info)
    assert response.available == 1
    assert response.requested == 2
    assert response.other_total_available == 5
    assert response.is_sufficient_in_total is True
    assert response.detail == (
        "Недостаточно остатка на выбранном складе: доступно 1, запрошено 2. "
        "На других активных складах доступно суммарно 5. Этого достаточно для операции. "
        "Склады-кандидаты: Other Warehouse (id=2): доступно 5."
    )


@pytest.mark.asyncio
async def test_fbs_reserve_raises_detailed_error_when_not_enough_in_total(
    mock_uow,
    product,
    warehouse,
    stock_low_available,
    fbs_reserve_input_no_key,
    movement_from_dto,
    other_warehouse_availability_empty,
) -> None:
    mock_uow.sku_repo.get_by_id.return_value = product
    mock_uow.warehouse_repo.get_by_id.return_value = warehouse
    mock_uow.stock_repo.get_by_product_and_warehouse.return_value = (
        product,
        stock_low_available,
        warehouse,
    )
    mock_uow.stock_repo.list_other_warehouses_availability.return_value = [
        other_warehouse_availability_empty
    ]
    mock_uow.movement_repo.add_movement.side_effect = movement_from_dto
    use_case = FbsReserveMovementUseCase(uow=mock_uow)

    with pytest.raises(InsufficientStockError) as exc:
        await use_case.execute(fbs_reserve_input_no_key)

    data = exc.value.data
    info = exc.value.info
    assert data is not None
    assert info is not None
    assert data["available"] == stock_low_available.qty_available
    assert data["requested"] == fbs_reserve_input_no_key.qty
    assert sum(item.qty_available for item in data["other_warehouses"]) == 0
    assert info.other_total_available == 0
    assert info.is_sufficient_in_total is False

    response = ErrorResponse.from_error_data(info)
    assert response.other_total_available == 0
    assert response.is_sufficient_in_total is False
    assert response.detail == (
        "Недостаточно остатка на выбранном складе: доступно 1, запрошено 2. "
        "На других активных складах доступно суммарно 0. Этого недостаточно для операции."
    )


@pytest.mark.asyncio
async def test_fbs_ship_raises_detailed_error_when_physical_shortage_but_enough_elsewhere(
    mock_uow,
    fbs_reserve_pending_movement,
    product,
    warehouse,
    stock_insufficient_physical_for_ship,
    fbs_ship_input,
    other_warehouse_availability_enough,
) -> None:
    mock_uow.movement_repo.get_movement.return_value = fbs_reserve_pending_movement
    mock_uow.warehouse_repo.get_by_id.return_value = warehouse
    mock_uow.stock_repo.get_by_product_and_warehouse.return_value = (
        product,
        stock_insufficient_physical_for_ship,
        warehouse,
    )
    mock_uow.stock_repo.list_other_warehouses_availability.return_value = [
        other_warehouse_availability_enough
    ]
    use_case = FbsShipMovementUseCase(uow=mock_uow)

    with pytest.raises(InsufficientStockError) as exc:
        await use_case.execute(fbs_ship_input)

    info = exc.value.info
    assert info is not None
    assert info.available == stock_insufficient_physical_for_ship.qty_physical
    assert info.requested == fbs_reserve_pending_movement.qty
    assert info.other_warehouses == [other_warehouse_availability_enough]
    assert info.other_total_available == 5
    assert info.is_sufficient_in_total is True

    response = ErrorResponse.from_error_data(info)
    assert response.detail == (
        "Недостаточно остатка на выбранном складе: доступно 1, запрошено 2. "
        "На других активных складах доступно суммарно 5. Этого достаточно для операции. "
        "Склады-кандидаты: Other Warehouse (id=2): доступно 5."
    )


@pytest.mark.asyncio
async def test_fbs_ship_is_idempotent_and_does_not_double_debit(
    mock_uow, product, warehouse
) -> None:
    stock = Stock(id=1, product_id=1, warehouse_id=1, qty_physical=10, qty_reserved_fbs=4)
    movement = Movement(
        id=70,
        product_id=1,
        type=MovementType.FBS_RESERVE,
        qty=2,
        from_warehouse_id=1,
        status=MovementStatus.PENDING,
        created_at=datetime.now(UTC),
    )
    mock_uow.movement_repo.get_movement.return_value = movement
    mock_uow.warehouse_repo.get_by_id.return_value = warehouse
    mock_uow.stock_repo.get_by_product_and_warehouse.return_value = (product, stock, warehouse)

    use_case = FbsShipMovementUseCase(uow=mock_uow)
    ship_input = FbsShipMovementInput(movement_id=70, idempotency_key="ship-key-1")

    result = await use_case.execute(ship_input)

    assert stock.qty_physical == 8
    assert stock.qty_reserved_fbs == 2
    assert result.type == MovementType.FBS_SHIP
    assert result.status == MovementStatus.IN_TRANSIT
    assert mock_uow.stock_repo.update.await_count == 1
    assert mock_uow.movement_repo.save_movement.await_count == 1

    with pytest.raises(DuplicateIdempotencyKeyError):
        await use_case.execute(ship_input)

    assert stock.qty_physical == 8
    assert stock.qty_reserved_fbs == 2
    assert mock_uow.stock_repo.update.await_count == 1
    assert mock_uow.movement_repo.save_movement.await_count == 1
