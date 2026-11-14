"""SQLAlchemy repository implementation for movements."""

from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dtos import CreateMovementDTO, ListMovementsDTO
from src.domain.entities import Movement
from src.domain.exceptions import EntityNotFoundError
from src.domain.interfaces import IMovementRepository
from src.infrastructure.models import MovementModel


class SqlAlchemyMovementRepository(IMovementRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_movement(self, data: CreateMovementDTO) -> Movement:
        model = MovementModel(
            product_id=data.product_id,
            type=data.type.value,
            qty=data.qty,
            from_warehouse_id=data.from_warehouse_id,
            to_warehouse_id=data.to_warehouse_id,
            status=data.status.value,
            idempotency_key=data.idempotency_key,
            completed_at=data.completed_at,
        )
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return model.to_entity()

    async def save_movement(self, movement: Movement) -> Movement:
        res = await self.session.execute(
            select(MovementModel).where(MovementModel.id == movement.id)
        )
        model = res.scalar_one()
        model.type = movement.type.value
        model.qty = movement.qty
        model.from_warehouse_id = movement.from_warehouse_id
        model.to_warehouse_id = movement.to_warehouse_id
        model.status = movement.status.value
        model.idempotency_key = movement.idempotency_key
        model.completed_at = movement.completed_at
        await self.session.flush()
        await self.session.refresh(model)
        return model.to_entity()

    async def get_movement(self, movement_id: int) -> Movement:
        res = await self.session.execute(
            select(MovementModel).where(MovementModel.id == movement_id)
        )
        model = res.scalar_one_or_none()
        if model is None:
            raise EntityNotFoundError(f"Movement not found: {movement_id}")
        return model.to_entity()

    async def get_by_idempotency_key(self, idempotency_key: str) -> Movement | None:
        if not idempotency_key:
            return None
        res = await self.session.execute(
            select(MovementModel).where(MovementModel.idempotency_key == idempotency_key)
        )
        model = res.scalar_one_or_none()
        return model.to_entity() if model else None

    async def list_movements(self, query: ListMovementsDTO) -> tuple[list[Movement], int]:
        page = query.page
        page_size = query.page_size
        stmt = select(MovementModel)
        count_stmt = select(func.count()).select_from(MovementModel)
        if query.product_id is not None:
            stmt = stmt.where(MovementModel.product_id == query.product_id)
            count_stmt = count_stmt.where(MovementModel.product_id == query.product_id)
        if query.movement_type:
            stmt = stmt.where(MovementModel.type == query.movement_type)
            count_stmt = count_stmt.where(MovementModel.type == query.movement_type)
        if query.status:
            stmt = stmt.where(MovementModel.status == query.status)
            count_stmt = count_stmt.where(MovementModel.status == query.status)
        if query.warehouse_id is not None:
            cond = or_(
                MovementModel.from_warehouse_id == query.warehouse_id,
                MovementModel.to_warehouse_id == query.warehouse_id,
            )
            stmt = stmt.where(cond)
            count_stmt = count_stmt.where(cond)
        if query.date_from:
            stmt = stmt.where(MovementModel.created_at >= query.date_from)
            count_stmt = count_stmt.where(MovementModel.created_at >= query.date_from)
        if query.date_to:
            stmt = stmt.where(MovementModel.created_at <= query.date_to)
            count_stmt = count_stmt.where(MovementModel.created_at <= query.date_to)

        total_res = await self.session.execute(count_stmt)
        total = int(total_res.scalar_one() or 0)
        stmt = (
            stmt.order_by(MovementModel.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        res = await self.session.execute(stmt)
        return [m.to_entity() for m in res.scalars().all()], total
