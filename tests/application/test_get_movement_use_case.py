from __future__ import annotations

import pytest

from src.application.usecases.movements.get_movement import GetMovementUseCase
from src.domain.entities import MovementStatus, MovementType
from src.domain.exceptions import EntityNotFoundError


@pytest.mark.asyncio
async def test_get_movement_returns_dto_when_movement_exists(mock_uow, get_movement_entity) -> None:
    mock_uow.movement_repo.get_movement.return_value = get_movement_entity
    use_case = GetMovementUseCase(uow=mock_uow)

    result = await use_case.execute(get_movement_entity.id)

    assert result.id == get_movement_entity.id
    assert result.type == MovementType.INBOUND.value
    assert result.qty == get_movement_entity.qty
    assert result.status == MovementStatus.COMPLETED.value
    mock_uow.movement_repo.get_movement.assert_awaited_once_with(get_movement_entity.id)


@pytest.mark.asyncio
@pytest.mark.parametrize("movement_id", [123, 0])
async def test_get_movement_raises_entity_not_found_when_movement_missing(
    mock_uow, movement_id: int
) -> None:
    mock_uow.movement_repo.get_movement.side_effect = EntityNotFoundError("not found")
    use_case = GetMovementUseCase(uow=mock_uow)

    with pytest.raises(EntityNotFoundError):
        await use_case.execute(movement_id)
