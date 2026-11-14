from __future__ import annotations

import pytest

from src.application.usecases.warehouses.create_warehouse import CreateWarehouseUseCase
from src.application.usecases.warehouses.delete_warehouse import DeleteWarehouseUseCase
from src.application.usecases.warehouses.update_warehouse import UpdateWarehouseUseCase
from src.domain.exceptions import EntityNotFoundError


@pytest.mark.asyncio
async def test_create_warehouse_returns_created_dto(
    mock_uow, warehouse, create_warehouse_input
) -> None:
    warehouse.id = 10
    warehouse.name = "WH"
    mock_uow.warehouse_repo.create.return_value = warehouse
    use_case = CreateWarehouseUseCase(uow=mock_uow)

    result = await use_case.execute(create_warehouse_input)

    assert result.id == 10
    assert result.name == "WH"
    assert result.is_deleted is False
    mock_uow.warehouse_repo.create.assert_awaited_once()
    assert mock_uow.warehouse_repo.create.await_args.args[0].name == "WH"


@pytest.mark.asyncio
async def test_update_warehouse_updates_name_when_found(
    mock_uow, warehouse, update_warehouse_input
) -> None:
    warehouse.id = 1
    warehouse.name = "Old"
    mock_uow.warehouse_repo.get_by_id.return_value = warehouse
    use_case = UpdateWarehouseUseCase(uow=mock_uow)

    result = await use_case.execute(update_warehouse_input)

    assert result.id == 1
    assert result.name == "New"
    mock_uow.warehouse_repo.update.assert_awaited_once_with(warehouse)


@pytest.mark.asyncio
async def test_update_warehouse_raises_entity_not_found_when_missing(
    mock_uow, update_warehouse_input
) -> None:
    mock_uow.warehouse_repo.get_by_id.side_effect = EntityNotFoundError("not found")
    use_case = UpdateWarehouseUseCase(uow=mock_uow)

    with pytest.raises(EntityNotFoundError):
        await use_case.execute(update_warehouse_input)


@pytest.mark.asyncio
async def test_delete_warehouse_soft_deletes_once_for_repeated_calls(mock_uow, warehouse) -> None:
    warehouse.id = 1
    warehouse.name = "WH"
    warehouse.is_deleted = False
    warehouse.deleted_at = None
    mock_uow.warehouse_repo.get_by_id.return_value = warehouse
    use_case = DeleteWarehouseUseCase(uow=mock_uow)

    first = await use_case.execute(warehouse.id)
    second = await use_case.execute(warehouse.id)

    assert first.is_deleted is True
    assert second.is_deleted is True
    assert warehouse.deleted_at is not None
    assert mock_uow.warehouse_repo.update.await_count == 1


@pytest.mark.asyncio
async def test_delete_warehouse_raises_entity_not_found_when_missing(mock_uow) -> None:
    mock_uow.warehouse_repo.get_by_id.side_effect = EntityNotFoundError("not found")
    use_case = DeleteWarehouseUseCase(uow=mock_uow)

    with pytest.raises(EntityNotFoundError):
        await use_case.execute(999)
