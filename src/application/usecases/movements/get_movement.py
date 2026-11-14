"""Get movement by id use case."""

from __future__ import annotations

from src.domain.entities import Movement
from src.domain.interfaces import IUnitOfWork


class GetMovementUseCase:
    def __init__(self, uow: IUnitOfWork) -> None:
        self.uow = uow

    async def execute(self, movement_id: int) -> Movement:
        return await self.uow.movement_repo.get_movement(movement_id)
