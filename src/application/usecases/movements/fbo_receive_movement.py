"""FBO receive movement use case."""

from __future__ import annotations

from src.application.dtos import FboReceiveMovementInput
from src.domain.entities import Movement, MovementStatus, MovementType
from src.domain.interfaces import IUnitOfWork


class FboReceiveMovementUseCase:
    def __init__(self, uow: IUnitOfWork) -> None:
        self.uow = uow

    async def execute(self, input_data: FboReceiveMovementInput) -> Movement:
        movement = await self.uow.movement_repo.get_movement(input_data.movement_id)
        movement.ensure_type(MovementType.FBO_OUT)

        if movement.is_completed():
            return movement

        movement.complete(status=MovementStatus.COMPLETED)
        return await self.uow.movement_repo.save_movement(movement)
