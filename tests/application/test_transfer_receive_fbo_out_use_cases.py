from __future__ import annotations

import pytest

from src.api.schemas import ErrorResponse
from src.application.dtos import CreateFboOutMovementInput
from src.application.usecases.movements.fbo_out_movement import FboOutMovementUseCase
from src.application.usecases.movements.receive_movement import ReceiveMovementUseCase
from src.application.usecases.movements.transfer_movement import TransferMovementUseCase
from src.domain.entities import MovementStatus, MovementType, Stock
from src.domain.exceptions import EntityNotFoundError, InsufficientStockError


@pytest.mark.asyncio
async def test_transfer_movement_returns_existing_for_idempotent_request(
    mock_uow, transfer_existing_movement, transfer_input
) -> None:
    mock_uow.movement_repo.get_by_idempotency_key.return_value = transfer_existing_movement
    use_case = TransferMovementUseCase(uow=mock_uow)

    result = await use_case.execute(transfer_input)

    assert result.id == transfer_existing_movement.id
    mock_uow.movement_repo.get_by_idempotency_key.assert_awaited_once_with(
        transfer_input.idempotency_key
    )
    mock_uow.movement_repo.add_movement.assert_not_called()
    mock_uow.sku_repo.get_by_id.assert_not_called()
    mock_uow.warehouse_repo.get_by_id.assert_not_called()
    mock_uow.stock_repo.get_by_product_and_warehouse_for_update.assert_not_called()
    mock_uow.stock_repo.create.assert_not_called()


@pytest.mark.asyncio
async def test_transfer_movement_raises_insufficient_stock_when_available_too_low(
    mock_uow,
    product,
    from_warehouse,
    to_warehouse,
    transfer_from_stock_low_available,
    transfer_input_no_key,
    movement_from_dto,
) -> None:
    mock_uow.sku_repo.get_by_id.return_value = product
    mock_uow.warehouse_repo.get_by_id.side_effect = [from_warehouse, to_warehouse]
    mock_uow.stock_repo.get_by_product_and_warehouse_for_update.return_value = (
        product,
        transfer_from_stock_low_available,
        from_warehouse,
    )
    mock_uow.movement_repo.add_movement.side_effect = movement_from_dto
    use_case = TransferMovementUseCase(uow=mock_uow)

    with pytest.raises(InsufficientStockError):
        await use_case.execute(transfer_input_no_key)


@pytest.mark.asyncio
async def test_transfer_movement_updates_stock_and_creates_in_transit_movement(
    mock_uow,
    product,
    from_warehouse,
    to_warehouse,
    transfer_from_stock,
    transfer_saved_movement,
    transfer_input_new,
) -> None:
    mock_uow.sku_repo.get_by_id.return_value = product
    mock_uow.warehouse_repo.get_by_id.side_effect = [from_warehouse, to_warehouse]
    mock_uow.stock_repo.get_by_product_and_warehouse_for_update.return_value = (
        product,
        transfer_from_stock,
        from_warehouse,
    )
    mock_uow.movement_repo.add_movement.return_value = transfer_saved_movement
    use_case = TransferMovementUseCase(uow=mock_uow)

    result = await use_case.execute(transfer_input_new)

    assert transfer_from_stock.qty_physical == 3
    assert result.type == MovementType.TRANSFER_OUT
    assert result.status == MovementStatus.IN_TRANSIT
    mock_uow.movement_repo.get_by_idempotency_key.assert_awaited_once_with(
        transfer_input_new.idempotency_key
    )
    mock_uow.stock_repo.update.assert_awaited_once_with(transfer_from_stock)


@pytest.mark.asyncio
async def test_receive_movement_raises_when_movement_not_found(
    mock_uow, receive_input_not_found
) -> None:
    mock_uow.movement_repo.get_movement.side_effect = EntityNotFoundError("not found")
    use_case = ReceiveMovementUseCase(uow=mock_uow)

    with pytest.raises(EntityNotFoundError):
        await use_case.execute(receive_input_not_found)


@pytest.mark.asyncio
async def test_receive_movement_is_noop_when_already_completed(
    mock_uow, receive_completed_movement, receive_input_completed
) -> None:
    mock_uow.movement_repo.get_movement.return_value = receive_completed_movement
    use_case = ReceiveMovementUseCase(uow=mock_uow)

    result = await use_case.execute(receive_input_completed)

    assert result.status == MovementStatus.COMPLETED
    mock_uow.stock_repo.get_by_product_and_warehouse_for_update.assert_not_called()
    mock_uow.stock_repo.create.assert_not_called()
    mock_uow.movement_repo.save_movement.assert_not_called()


@pytest.mark.asyncio
async def test_receive_movement_updates_destination_stock_and_completes(
    mock_uow,
    receive_in_transit_movement,
    product,
    destination_warehouse,
    destination_stock,
    receive_input_in_transit,
) -> None:
    mock_uow.movement_repo.get_movement.return_value = receive_in_transit_movement
    mock_uow.warehouse_repo.get_by_id.return_value = destination_warehouse
    mock_uow.stock_repo.get_by_product_and_warehouse_for_update.return_value = (
        product,
        destination_stock,
        destination_warehouse,
    )
    use_case = ReceiveMovementUseCase(uow=mock_uow)

    result = await use_case.execute(receive_input_in_transit)

    assert destination_stock.qty_physical == 3
    assert result.status == MovementStatus.COMPLETED
    assert receive_in_transit_movement.completed_at is not None
    mock_uow.stock_repo.update.assert_awaited_once_with(destination_stock)


@pytest.mark.asyncio
async def test_fbo_out_movement_returns_existing_for_idempotent_request(
    mock_uow, fbo_out_existing_movement, fbo_out_input
) -> None:
    mock_uow.movement_repo.get_by_idempotency_key.return_value = fbo_out_existing_movement
    use_case = FboOutMovementUseCase(uow=mock_uow)

    result = await use_case.execute(fbo_out_input)

    assert result.id == fbo_out_existing_movement.id
    mock_uow.movement_repo.get_by_idempotency_key.assert_awaited_once_with(
        fbo_out_input.idempotency_key
    )
    mock_uow.movement_repo.add_movement.assert_not_called()
    mock_uow.sku_repo.get_by_id.assert_not_called()
    mock_uow.warehouse_repo.get_by_id.assert_not_called()
    mock_uow.stock_repo.get_by_product_and_warehouse_for_update.assert_not_called()
    mock_uow.stock_repo.create.assert_not_called()


@pytest.mark.asyncio
async def test_fbo_out_movement_raises_insufficient_stock_when_qty_exceeds_available(
    mock_uow, product, warehouse, stock_no_reserve, fbo_out_input_no_key, movement_from_dto
) -> None:
    mock_uow.sku_repo.get_by_id.return_value = product
    mock_uow.warehouse_repo.get_by_id.return_value = warehouse
    mock_uow.stock_repo.get_by_product_and_warehouse_for_update.return_value = (
        product,
        stock_no_reserve,
        warehouse,
    )
    mock_uow.movement_repo.add_movement.side_effect = movement_from_dto
    use_case = FboOutMovementUseCase(uow=mock_uow)

    with pytest.raises(InsufficientStockError):
        await use_case.execute(fbo_out_input_no_key)


@pytest.mark.asyncio
async def test_transfer_movement_raises_when_source_warehouse_is_deleted(
    mock_uow, product, to_warehouse, transfer_input_no_key, movement_from_dto
) -> None:
    mock_uow.sku_repo.get_by_id.return_value = product
    mock_uow.warehouse_repo.get_by_id.side_effect = [EntityNotFoundError("not found"), to_warehouse]
    mock_uow.movement_repo.add_movement.side_effect = movement_from_dto
    use_case = TransferMovementUseCase(uow=mock_uow)

    with pytest.raises(EntityNotFoundError):
        await use_case.execute(transfer_input_no_key)

    mock_uow.stock_repo.get_by_product_and_warehouse_for_update.assert_not_called()
    mock_uow.stock_repo.create.assert_not_called()
    mock_uow.movement_repo.add_movement.assert_awaited_once()


@pytest.mark.asyncio
async def test_transfer_movement_raises_detailed_error_when_enough_on_other_warehouses(
    mock_uow,
    product,
    from_warehouse,
    to_warehouse,
    transfer_from_stock_low_available,
    transfer_input_no_key,
    movement_from_dto,
    other_warehouse_availability_enough_id3,
) -> None:
    mock_uow.sku_repo.get_by_id.return_value = product
    mock_uow.warehouse_repo.get_by_id.side_effect = [from_warehouse, to_warehouse]
    mock_uow.stock_repo.get_by_product_and_warehouse_for_update.return_value = (
        product,
        transfer_from_stock_low_available,
        from_warehouse,
    )
    mock_uow.stock_repo.list_other_warehouses_availability.return_value = [
        other_warehouse_availability_enough_id3
    ]
    mock_uow.movement_repo.add_movement.side_effect = movement_from_dto
    use_case = TransferMovementUseCase(uow=mock_uow)

    with pytest.raises(InsufficientStockError) as exc:
        await use_case.execute(transfer_input_no_key)

    info = exc.value.info
    assert info is not None
    assert info.available == transfer_from_stock_low_available.qty_available
    assert info.requested == transfer_input_no_key.qty
    assert info.other_warehouses == [other_warehouse_availability_enough_id3]
    assert info.other_total_available == 5
    assert info.is_sufficient_in_total is True

    response = ErrorResponse.from_error_data(info)
    assert response.other_total_available == 5
    assert response.is_sufficient_in_total is True
    assert response.detail == (
        "Недостаточно остатка на выбранном складе: доступно 1, запрошено 2. "
        "На других активных складах доступно суммарно 5. Этого достаточно для операции. "
        "Склады-кандидаты: Other Warehouse (id=3): доступно 5."
    )


@pytest.mark.asyncio
async def test_fbo_out_movement_raises_detailed_error_when_not_enough_in_total(
    mock_uow,
    product,
    warehouse,
    stock_no_reserve,
    fbo_out_input_no_key,
    movement_from_dto,
    other_warehouse_availability_empty,
) -> None:
    mock_uow.sku_repo.get_by_id.return_value = product
    mock_uow.warehouse_repo.get_by_id.return_value = warehouse
    mock_uow.stock_repo.get_by_product_and_warehouse_for_update.return_value = (
        product,
        stock_no_reserve,
        warehouse,
    )
    mock_uow.stock_repo.list_other_warehouses_availability.return_value = [
        other_warehouse_availability_empty
    ]
    mock_uow.movement_repo.add_movement.side_effect = movement_from_dto
    use_case = FboOutMovementUseCase(uow=mock_uow)

    with pytest.raises(InsufficientStockError) as exc:
        await use_case.execute(fbo_out_input_no_key)

    info = exc.value.info
    assert info is not None
    assert info.available == stock_no_reserve.qty_available
    assert info.requested == fbo_out_input_no_key.qty
    assert info.other_warehouses == [other_warehouse_availability_empty]
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
async def test_fbo_out_movement_rejects_when_available_less_than_requested_due_to_reserve(
    mock_uow, product, warehouse, movement_from_dto
) -> None:
    stock = Stock(id=1, product_id=1, warehouse_id=1, qty_physical=10, qty_reserved_fbs=8)
    mock_uow.sku_repo.get_by_id.return_value = product
    mock_uow.warehouse_repo.get_by_id.return_value = warehouse
    mock_uow.stock_repo.get_by_product_and_warehouse_for_update.return_value = (
        product,
        stock,
        warehouse,
    )
    mock_uow.movement_repo.add_movement.side_effect = movement_from_dto
    use_case = FboOutMovementUseCase(uow=mock_uow)

    with pytest.raises(InsufficientStockError) as exc:
        await use_case.execute(
            CreateFboOutMovementInput(
                product_id=1, from_warehouse_id=1, qty=3, idempotency_key=None
            )
        )

    info = exc.value.info
    assert info is not None
    assert info.available == 2
    assert info.requested == 3
    assert stock.qty_physical == 10
    assert stock.qty_reserved_fbs == 8
    mock_uow.stock_repo.update.assert_not_called()
