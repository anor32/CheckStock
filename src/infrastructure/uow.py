from __future__ import annotations

from typing import Any, Self

from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.interfaces import (
    IMovementRepository,
    ISkuRepository,
    IStockRepository,
    IUnitOfWork,
    IWarehouseRepository,
)
from src.infrastructure.repositories.movement_repository import SqlAlchemyMovementRepository
from src.infrastructure.repositories.sku_repository import SqlAlchemySkuRepository
from src.infrastructure.repositories.stock_repository import SqlAlchemyStockRepository
from src.infrastructure.repositories.warehouse_repository import SqlAlchemyWarehouseRepository


class SqlAlchemyUnitOfWork(IUnitOfWork):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.sku_repo: ISkuRepository = SqlAlchemySkuRepository(session)
        self.warehouse_repo: IWarehouseRepository = SqlAlchemyWarehouseRepository(session)
        self.stock_repo: IStockRepository = SqlAlchemyStockRepository(session)
        self.movement_repo: IMovementRepository = SqlAlchemyMovementRepository(session)
        self._active = False

    async def __aenter__(self) -> Self:
        self._active = True
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        try:
            if exc_type:
                await self.rollback()
            else:
                await self.commit()
        finally:
            self._active = False

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()

    def begin_nested(self) -> Any:
        return self.session.begin_nested()
