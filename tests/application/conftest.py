from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest

from src.application.dtos import (
    CreateFboOutMovementInput,
    CreateFbsReserveMovementInput,
    CreateInboundMovementInput,
    CreateTransferMovementInput,
    FboReceiveMovementInput,
    FbsCancelMovementInput,
    FbsShipMovementInput,
    ReceiveMovementInput,
)
from src.domain.entities import (
    Movement,
    MovementStatus,
    MovementType,
    Product,
    Stock,
    Warehouse,
    WarehouseStockAvailability,
)


@pytest.fixture
def mock_uow() -> Mock:
    uow = Mock()
    uow.sku_repo = Mock()
    uow.warehouse_repo = Mock()
    uow.stock_repo = Mock()
    uow.movement_repo = Mock()

    uow.sku_repo.get_by_id = AsyncMock()
    uow.sku_repo.get_by_sku = AsyncMock()
    uow.sku_repo.add = AsyncMock()
    uow.sku_repo.list_all = AsyncMock()

    uow.warehouse_repo.get_by_id = AsyncMock()
    uow.warehouse_repo.create = AsyncMock()
    uow.warehouse_repo.update = AsyncMock(side_effect=lambda obj: obj)
    uow.warehouse_repo.list_all = AsyncMock()

    uow.stock_repo.get_by_product_and_warehouse = AsyncMock()
    uow.stock_repo.list_stocks = AsyncMock()
    uow.stock_repo.get_by_id = AsyncMock()
    uow.stock_repo.update = AsyncMock(side_effect=lambda obj: obj)
    uow.stock_repo.create = AsyncMock()
    uow.stock_repo.list_other_warehouses_availability = AsyncMock(return_value=[])

    uow.movement_repo.add_movement = AsyncMock()
    uow.movement_repo.save_movement = AsyncMock(side_effect=lambda obj: obj)
    uow.movement_repo.get_movement = AsyncMock()
    uow.movement_repo.get_by_idempotency_key = AsyncMock(return_value=None)
    uow.movement_repo.list_movements = AsyncMock()

    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()
    return uow


@pytest.fixture
def product() -> Product:
    return Product(id=1, sku="SKU-1", name="Product")


@pytest.fixture
def created_product() -> Product:
    return Product(id=10, sku="SKU-NEW", name="New product")


@pytest.fixture
def warehouse() -> Warehouse:
    return Warehouse(id=1, name="Warehouse")


@pytest.fixture
def inbound_warehouse() -> Warehouse:
    return Warehouse(id=2, name="Warehouse")


@pytest.fixture
def from_warehouse() -> Warehouse:
    return Warehouse(id=1, name="From Warehouse")


@pytest.fixture
def to_warehouse() -> Warehouse:
    return Warehouse(id=2, name="To Warehouse")


@pytest.fixture
def destination_warehouse() -> Warehouse:
    return Warehouse(id=2, name="Destination Warehouse")


@pytest.fixture
def stock() -> Stock:
    return Stock(id=1, product_id=1, warehouse_id=1, qty_physical=5, qty_reserved_fbs=1)


@pytest.fixture
def stock_low_available() -> Stock:
    return Stock(id=1, product_id=1, warehouse_id=1, qty_physical=5, qty_reserved_fbs=4)


@pytest.fixture
def stock_for_ship() -> Stock:
    return Stock(id=1, product_id=1, warehouse_id=1, qty_physical=5, qty_reserved_fbs=2)


@pytest.fixture
def stock_insufficient_physical_for_ship() -> Stock:
    return Stock(id=1, product_id=1, warehouse_id=1, qty_physical=1, qty_reserved_fbs=2)


@pytest.fixture
def stock_no_reserve() -> Stock:
    return Stock(id=1, product_id=1, warehouse_id=1, qty_physical=1, qty_reserved_fbs=0)


@pytest.fixture
def transfer_from_stock() -> Stock:
    return Stock(id=10, product_id=1, warehouse_id=1, qty_physical=5, qty_reserved_fbs=1)


@pytest.fixture
def transfer_from_stock_low_available() -> Stock:
    return Stock(id=10, product_id=1, warehouse_id=1, qty_physical=5, qty_reserved_fbs=4)


@pytest.fixture
def inbound_stock() -> Stock:
    return Stock(id=3, product_id=1, warehouse_id=2, qty_physical=5, qty_reserved_fbs=0)


@pytest.fixture
def destination_stock() -> Stock:
    return Stock(id=30, product_id=1, warehouse_id=2, qty_physical=1, qty_reserved_fbs=0)


@pytest.fixture
def other_warehouse_availability_enough() -> WarehouseStockAvailability:
    return WarehouseStockAvailability(
        warehouse_id=2,
        warehouse_name="Other Warehouse",
        qty_available=5,
        qty_physical=5,
        qty_reserved_fbs=0,
    )


@pytest.fixture
def other_warehouse_availability_empty() -> WarehouseStockAvailability:
    return WarehouseStockAvailability(
        warehouse_id=2,
        warehouse_name="Other Warehouse",
        qty_available=0,
        qty_physical=0,
        qty_reserved_fbs=0,
    )


@pytest.fixture
def other_warehouse_availability_enough_id3() -> WarehouseStockAvailability:
    return WarehouseStockAvailability(
        warehouse_id=3,
        warehouse_name="Other Warehouse",
        qty_available=5,
        qty_physical=5,
        qty_reserved_fbs=0,
    )


@pytest.fixture
def movement_from_dto() -> Callable[[Any], Movement]:
    def _factory(dto: Any) -> Movement:
        return Movement(
            id=1,
            product_id=dto.product_id,
            type=dto.type,
            qty=dto.qty,
            from_warehouse_id=getattr(dto, "from_warehouse_id", None),
            to_warehouse_id=getattr(dto, "to_warehouse_id", None),
            status=getattr(dto, "status", MovementStatus.PENDING),
            idempotency_key=getattr(dto, "idempotency_key", None),
            created_at=datetime.now(UTC),
            completed_at=None,
        )

    return _factory


@pytest.fixture
def fbo_receive_completed_movement() -> Movement:
    return Movement(
        id=50,
        product_id=1,
        type=MovementType.FBO_OUT,
        qty=1,
        from_warehouse_id=1,
        status=MovementStatus.COMPLETED,
        idempotency_key="r1",
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def fbo_receive_in_transit_movement() -> Movement:
    return Movement(
        id=50,
        product_id=1,
        type=MovementType.FBO_OUT,
        qty=1,
        from_warehouse_id=1,
        status=MovementStatus.IN_TRANSIT,
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def fbs_reserve_existing_movement() -> Movement:
    return Movement(
        id=60,
        product_id=1,
        type=MovementType.FBS_RESERVE,
        qty=2,
        from_warehouse_id=1,
        status=MovementStatus.PENDING,
        idempotency_key="res1",
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def fbs_reserve_saved_movement() -> Movement:
    return Movement(
        id=60,
        product_id=1,
        type=MovementType.FBS_RESERVE,
        qty=2,
        from_warehouse_id=1,
        status=MovementStatus.PENDING,
        idempotency_key="k",
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def fbs_ship_in_transit_movement() -> Movement:
    return Movement(
        id=70,
        product_id=1,
        type=MovementType.FBS_SHIP,
        qty=2,
        from_warehouse_id=1,
        status=MovementStatus.IN_TRANSIT,
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def fbs_reserve_pending_movement() -> Movement:
    return Movement(
        id=70,
        product_id=1,
        type=MovementType.FBS_RESERVE,
        qty=2,
        from_warehouse_id=1,
        status=MovementStatus.PENDING,
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def fbs_cancelled_movement() -> Movement:
    return Movement(
        id=80,
        product_id=1,
        type=MovementType.FBS_RESERVE,
        qty=2,
        from_warehouse_id=1,
        status=MovementStatus.CANCELLED,
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def fbs_cancel_pending_movement() -> Movement:
    return Movement(
        id=80,
        product_id=1,
        type=MovementType.FBS_RESERVE,
        qty=2,
        from_warehouse_id=1,
        status=MovementStatus.PENDING,
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def transfer_existing_movement() -> Movement:
    return Movement(
        id=11,
        product_id=1,
        type=MovementType.TRANSFER_OUT,
        qty=2,
        from_warehouse_id=1,
        to_warehouse_id=2,
        status=MovementStatus.IN_TRANSIT,
        idempotency_key="t1",
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def transfer_saved_movement() -> Movement:
    return Movement(
        id=20,
        product_id=1,
        type=MovementType.TRANSFER_OUT,
        qty=2,
        from_warehouse_id=1,
        to_warehouse_id=2,
        status=MovementStatus.IN_TRANSIT,
        idempotency_key="k",
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def receive_completed_movement() -> Movement:
    return Movement(
        id=5,
        product_id=1,
        type=MovementType.TRANSFER_OUT,
        qty=2,
        from_warehouse_id=1,
        to_warehouse_id=2,
        status=MovementStatus.COMPLETED,
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def receive_in_transit_movement() -> Movement:
    return Movement(
        id=6,
        product_id=1,
        type=MovementType.TRANSFER_OUT,
        qty=2,
        from_warehouse_id=1,
        to_warehouse_id=2,
        status=MovementStatus.IN_TRANSIT,
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def fbo_out_existing_movement() -> Movement:
    return Movement(
        id=40,
        product_id=1,
        type=MovementType.FBO_OUT,
        qty=1,
        from_warehouse_id=1,
        status=MovementStatus.IN_TRANSIT,
        idempotency_key="f1",
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def inbound_existing_movement() -> Movement:
    return Movement(
        id=99,
        product_id=1,
        type=MovementType.INBOUND,
        qty=7,
        from_warehouse_id=None,
        to_warehouse_id=2,
        status=MovementStatus.COMPLETED,
        idempotency_key="idem-1",
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def inbound_saved_movement() -> Movement:
    return Movement(
        id=77,
        product_id=1,
        type=MovementType.INBOUND,
        qty=4,
        from_warehouse_id=None,
        to_warehouse_id=2,
        status=MovementStatus.COMPLETED,
        idempotency_key="k2",
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def get_movement_entity() -> Movement:
    return Movement(
        id=1,
        product_id=2,
        type=MovementType.INBOUND,
        qty=5,
        to_warehouse_id=3,
        status=MovementStatus.COMPLETED,
        idempotency_key="k1",
        created_at=datetime.now(UTC),
    )


# Input DTO fixtures (use case inputs)
@pytest.fixture
def create_product_input() -> Any:
    from src.application.dtos import CreateProductInput

    return CreateProductInput(sku="SKU-NEW", name="New product")


@pytest.fixture
def create_product_duplicate_input() -> Any:
    from src.application.dtos import CreateProductInput

    return CreateProductInput(sku="SKU-1", name="Another name")


@pytest.fixture
def create_warehouse_input() -> Any:
    from src.application.dtos import CreateWarehouseInput

    return CreateWarehouseInput(name="WH")


@pytest.fixture
def update_warehouse_input() -> Any:
    from src.application.dtos import UpdateWarehouseInput

    return UpdateWarehouseInput(warehouse_id=1, name="New")


@pytest.fixture
def inbound_input() -> CreateInboundMovementInput:
    return CreateInboundMovementInput(product_id=1, warehouse_id=2, qty=7, idempotency_key="idem-1")


@pytest.fixture
def inbound_input_new() -> CreateInboundMovementInput:
    return CreateInboundMovementInput(product_id=1, warehouse_id=2, qty=4, idempotency_key="k2")


@pytest.fixture
def inbound_input_no_key() -> CreateInboundMovementInput:
    return CreateInboundMovementInput(product_id=1, warehouse_id=2, qty=1, idempotency_key=None)


@pytest.fixture
def transfer_input() -> CreateTransferMovementInput:
    return CreateTransferMovementInput(
        product_id=1, from_warehouse_id=1, to_warehouse_id=2, qty=2, idempotency_key="t1"
    )


@pytest.fixture
def transfer_input_new() -> CreateTransferMovementInput:
    return CreateTransferMovementInput(
        product_id=1, from_warehouse_id=1, to_warehouse_id=2, qty=2, idempotency_key="k"
    )


@pytest.fixture
def transfer_input_no_key() -> CreateTransferMovementInput:
    return CreateTransferMovementInput(
        product_id=1, from_warehouse_id=1, to_warehouse_id=2, qty=2, idempotency_key=None
    )


@pytest.fixture
def fbo_out_input() -> CreateFboOutMovementInput:
    return CreateFboOutMovementInput(product_id=1, from_warehouse_id=1, qty=1, idempotency_key="f1")


@pytest.fixture
def fbo_out_input_no_key() -> CreateFboOutMovementInput:
    return CreateFboOutMovementInput(product_id=1, from_warehouse_id=1, qty=2, idempotency_key=None)


@pytest.fixture
def fbs_reserve_input() -> CreateFbsReserveMovementInput:
    return CreateFbsReserveMovementInput(
        product_id=1, warehouse_id=1, qty=2, idempotency_key="res1"
    )


@pytest.fixture
def fbs_reserve_input_new() -> CreateFbsReserveMovementInput:
    return CreateFbsReserveMovementInput(product_id=1, warehouse_id=1, qty=2, idempotency_key="k")


@pytest.fixture
def fbs_reserve_input_no_key() -> CreateFbsReserveMovementInput:
    return CreateFbsReserveMovementInput(product_id=1, warehouse_id=1, qty=2, idempotency_key=None)


@pytest.fixture
def fbo_receive_input() -> FboReceiveMovementInput:
    return FboReceiveMovementInput(movement_id=50, idempotency_key="r1")


@pytest.fixture
def fbo_receive_input_no_key() -> FboReceiveMovementInput:
    return FboReceiveMovementInput(movement_id=50)


@pytest.fixture
def fbs_ship_input() -> FbsShipMovementInput:
    return FbsShipMovementInput(movement_id=70)


@pytest.fixture
def fbs_cancel_input() -> FbsCancelMovementInput:
    return FbsCancelMovementInput(movement_id=80)


@pytest.fixture
def receive_input_not_found() -> ReceiveMovementInput:
    return ReceiveMovementInput(movement_id=1)


@pytest.fixture
def receive_input_completed() -> ReceiveMovementInput:
    return ReceiveMovementInput(movement_id=5)


@pytest.fixture
def receive_input_in_transit() -> ReceiveMovementInput:
    return ReceiveMovementInput(movement_id=6)
