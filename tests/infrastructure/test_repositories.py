from __future__ import annotations

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dtos import CreateMovementDTO, CreateProductDTO, CreateWarehouseDTO
from src.domain.entities import MovementStatus, MovementType
from src.domain.exceptions import ProductAlreadyExistsError, ProductNotFoundError
from src.infrastructure.models import MovementModel, ProductModel, WarehouseModel
from src.infrastructure.repositories.movement_repository import SqlAlchemyMovementRepository
from src.infrastructure.repositories.sku_repository import SqlAlchemySkuRepository
from src.infrastructure.repositories.warehouse_repository import SqlAlchemyWarehouseRepository

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_sku_repository_add_and_get_by_sku(
    db_session: AsyncSession, sku_repo: SqlAlchemySkuRepository
) -> None:
    created = await sku_repo.add(CreateProductDTO(sku="SKU-X", name="Name"))

    assert created.sku == "SKU-X"
    assert created.id is not None

    await db_session.commit()
    found = await sku_repo.get_by_sku("SKU-X")

    assert found is not None
    assert found.id == created.id


@pytest.mark.asyncio
async def test_sku_repository_raises_for_missing_sku(sku_repo: SqlAlchemySkuRepository) -> None:
    with pytest.raises(ProductNotFoundError):
        await sku_repo.get_by_sku("MISSING-SKU")


@pytest.mark.asyncio
async def test_sku_repository_add_rejects_duplicate_sku(
    db_session: AsyncSession, sku_repo: SqlAlchemySkuRepository
) -> None:
    await sku_repo.add(CreateProductDTO(sku="SKU-DUP", name="Name 1"))
    await db_session.flush()

    with pytest.raises(ProductAlreadyExistsError):
        await sku_repo.add(CreateProductDTO(sku="SKU-DUP", name="Name 2"))


@pytest.mark.asyncio
async def test_warehouse_repository_create_persists_warehouse(
    db_session: AsyncSession, warehouse_repo: SqlAlchemyWarehouseRepository
) -> None:
    created = await warehouse_repo.create(CreateWarehouseDTO(name="WH-1"))
    await db_session.flush()

    assert created.id is not None
    assert created.name == "WH-1"
    count = await db_session.scalar(select(func.count()).select_from(WarehouseModel))
    assert count == 1


@pytest.mark.asyncio
async def test_movement_repository_add_movement_persists_movement(
    movement_repo: SqlAlchemyMovementRepository,
    persisted_product: ProductModel,
    persisted_warehouse: WarehouseModel,
) -> None:
    movement = CreateMovementDTO(
        product_id=persisted_product.id,
        type=MovementType.FBS_RESERVE,
        qty=2,
        from_warehouse_id=persisted_warehouse.id,
        status=MovementStatus.PENDING,
    )
    saved = await movement_repo.add_movement(movement)

    assert saved.id is not None
    assert saved.qty == 2
    assert saved.type == MovementType.FBS_RESERVE


@pytest.mark.asyncio
async def test_movement_repository_get_by_idempotency_key_returns_existing(
    db_session: AsyncSession,
    movement_repo: SqlAlchemyMovementRepository,
    persisted_product: ProductModel,
    persisted_warehouse: WarehouseModel,
) -> None:
    movement = CreateMovementDTO(
        product_id=persisted_product.id,
        type=MovementType.FBS_RESERVE,
        qty=2,
        from_warehouse_id=persisted_warehouse.id,
        status=MovementStatus.PENDING,
        idempotency_key="move-key-1",
    )
    first = await movement_repo.add_movement(movement)
    await db_session.flush()

    found = await movement_repo.get_by_idempotency_key("move-key-1")
    assert found is not None
    assert found.id == first.id
    assert found.idempotency_key == "move-key-1"

    missing = await movement_repo.get_by_idempotency_key("missing-key")
    assert missing is None

    count = await db_session.scalar(
        select(func.count())
        .select_from(MovementModel)
        .where(MovementModel.idempotency_key == "move-key-1")
    )
    assert count == 1
