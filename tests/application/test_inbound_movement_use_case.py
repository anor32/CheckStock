from __future__ import annotations

import pytest

from src.application.usecases.movements.inbound_movement import InboundMovementUseCase
from src.domain.entities import MovementStatus, MovementType
from src.domain.exceptions import EntityNotFoundError, ProductNotFoundError


@pytest.mark.asyncio
async def test_inbound_movement_returns_existing_for_idempotent_request(
    mock_uow, inbound_existing_movement, inbound_input
) -> None:
    mock_uow.movement_repo.get_by_idempotency_key.return_value = inbound_existing_movement
    use_case = InboundMovementUseCase(uow=mock_uow)

    result = await use_case.execute(inbound_input)

    assert result.id == inbound_existing_movement.id
    mock_uow.movement_repo.get_by_idempotency_key.assert_awaited_once_with(
        inbound_input.idempotency_key
    )
    mock_uow.movement_repo.add_movement.assert_not_called()
    mock_uow.sku_repo.get_by_id.assert_not_called()
    mock_uow.warehouse_repo.get_by_id.assert_not_called()
    mock_uow.stock_repo.get_by_product_and_warehouse_for_update.assert_not_called()
    mock_uow.stock_repo.create.assert_not_called()
    mock_uow.stock_repo.update.assert_not_called()


@pytest.mark.asyncio
async def test_inbound_movement_raises_when_product_not_found(
    mock_uow, inbound_warehouse, inbound_input_no_key, movement_from_dto
) -> None:
    mock_uow.movement_repo.add_movement.side_effect = movement_from_dto
    mock_uow.sku_repo.get_by_id.side_effect = ProductNotFoundError("not found")
    mock_uow.warehouse_repo.get_by_id.return_value = inbound_warehouse
    use_case = InboundMovementUseCase(uow=mock_uow)

    with pytest.raises(ProductNotFoundError):
        await use_case.execute(inbound_input_no_key)


@pytest.mark.asyncio
async def test_inbound_movement_raises_when_warehouse_not_found(
    mock_uow, product, inbound_input_no_key, movement_from_dto
) -> None:
    mock_uow.movement_repo.add_movement.side_effect = movement_from_dto
    mock_uow.sku_repo.get_by_id.return_value = product
    mock_uow.warehouse_repo.get_by_id.side_effect = EntityNotFoundError("not found")
    use_case = InboundMovementUseCase(uow=mock_uow)

    with pytest.raises(EntityNotFoundError):
        await use_case.execute(inbound_input_no_key)


@pytest.mark.asyncio
async def test_inbound_movement_creates_movement_and_updates_stock(
    mock_uow,
    product,
    inbound_warehouse,
    inbound_stock,
    inbound_saved_movement,
    inbound_input_new,
) -> None:
    mock_uow.sku_repo.get_by_id.return_value = product
    mock_uow.warehouse_repo.get_by_id.return_value = inbound_warehouse
    mock_uow.stock_repo.get_by_product_and_warehouse_for_update.return_value = (
        product,
        inbound_stock,
        inbound_warehouse,
    )
    mock_uow.movement_repo.add_movement.return_value = inbound_saved_movement
    use_case = InboundMovementUseCase(uow=mock_uow)

    result = await use_case.execute(inbound_input_new)

    assert inbound_stock.qty_physical == 9
    assert result.id == inbound_saved_movement.id
    assert result.type == MovementType.INBOUND
    assert result.status == MovementStatus.COMPLETED
    mock_uow.stock_repo.update.assert_awaited_once_with(inbound_stock)
    mock_uow.movement_repo.get_by_idempotency_key.assert_awaited_once_with(
        inbound_input_new.idempotency_key
    )
    mock_uow.movement_repo.add_movement.assert_awaited_once()


@pytest.mark.asyncio
async def test_inbound_movement_raises_when_warehouse_is_deleted(
    mock_uow, product, inbound_input_no_key, movement_from_dto
) -> None:
    mock_uow.movement_repo.add_movement.side_effect = movement_from_dto
    mock_uow.sku_repo.get_by_id.return_value = product
    mock_uow.warehouse_repo.get_by_id.side_effect = EntityNotFoundError("not found")
    use_case = InboundMovementUseCase(uow=mock_uow)

    with pytest.raises(EntityNotFoundError):
        await use_case.execute(inbound_input_no_key)

    mock_uow.stock_repo.get_by_product_and_warehouse_for_update.assert_not_called()
    mock_uow.stock_repo.create.assert_not_called()
    mock_uow.movement_repo.add_movement.assert_awaited_once()
