from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.models import ProductModel, WarehouseModel
from src.infrastructure.repositories.movement_repository import SqlAlchemyMovementRepository
from src.infrastructure.repositories.sku_repository import SqlAlchemySkuRepository
from src.infrastructure.repositories.warehouse_repository import SqlAlchemyWarehouseRepository


@pytest.fixture
def sku_repo(db_session: AsyncSession) -> SqlAlchemySkuRepository:
    return SqlAlchemySkuRepository(db_session)


@pytest.fixture
def warehouse_repo(db_session: AsyncSession) -> SqlAlchemyWarehouseRepository:
    return SqlAlchemyWarehouseRepository(db_session)


@pytest.fixture
def movement_repo(db_session: AsyncSession) -> SqlAlchemyMovementRepository:
    return SqlAlchemyMovementRepository(db_session)


@pytest.fixture
async def persisted_product(db_session: AsyncSession) -> ProductModel:
    product = ProductModel(sku="SKU-M", name="PM")
    db_session.add(product)
    await db_session.flush()
    return product


@pytest.fixture
async def persisted_warehouse(db_session: AsyncSession) -> WarehouseModel:
    warehouse = WarehouseModel(name="WH-M")
    db_session.add(warehouse)
    await db_session.flush()
    return warehouse
