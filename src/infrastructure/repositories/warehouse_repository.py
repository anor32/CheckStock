"""SQLAlchemy repository implementation for warehouses."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import Warehouse
from src.domain.exceptions import EntityNotFoundError
from src.domain.interfaces import IWarehouseRepository
from src.infrastructure.models import WarehouseModel


class SqlAlchemyWarehouseRepository(IWarehouseRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, warehouse_id: int, include_deleted: bool = False) -> Warehouse:
        stmt = select(WarehouseModel).where(WarehouseModel.id == warehouse_id)
        if not include_deleted:
            stmt = stmt.where(WarehouseModel.is_deleted.is_(False))
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()
        if model is None:
            raise EntityNotFoundError(f"Warehouse not found: {warehouse_id}")
        return model.to_entity()

    async def create(self, warehouse: Warehouse) -> Warehouse:
        if warehouse.idempotency_key:
            existing = await self._get_by_idempotency_key(warehouse.idempotency_key)
            if existing:
                return existing
        model = WarehouseModel.from_entity(warehouse)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return model.to_entity()

    async def _get_by_idempotency_key(self, idempotency_key: str | None) -> Warehouse | None:
        if not idempotency_key:
            return None
        res = await self.session.execute(
            select(WarehouseModel).where(WarehouseModel.idempotency_key == idempotency_key)
        )
        model = res.scalar_one_or_none()
        return model.to_entity() if model else None

    async def update(self, warehouse: Warehouse) -> Warehouse:
        if warehouse.id is None:
            raise ValueError("Warehouse must have id to update")
        res = await self.session.execute(
            select(WarehouseModel).where(WarehouseModel.id == warehouse.id)
        )
        model = res.scalar_one()
        model.name = warehouse.name
        model.is_deleted = warehouse.is_deleted
        model.deleted_at = warehouse.deleted_at
        model.idempotency_key = warehouse.idempotency_key
        await self.session.flush()
        await self.session.refresh(model)
        return model.to_entity()

    async def list_all(self, include_deleted: bool = True) -> list[Warehouse]:
        stmt = select(WarehouseModel).order_by(WarehouseModel.id)
        if not include_deleted:
            stmt = stmt.where(WarehouseModel.is_deleted.is_(False))
        res = await self.session.execute(stmt)
        return [m.to_entity() for m in res.scalars().all()]
