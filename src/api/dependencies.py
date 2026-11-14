"""FastAPI dependency providers (composition root)."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.usecases import (
    CreateProductUseCase,
    CreateWarehouseUseCase,
    DeleteWarehouseUseCase,
    FboOutMovementUseCase,
    FboReceiveMovementUseCase,
    FbsCancelMovementUseCase,
    FbsReserveMovementUseCase,
    FbsShipMovementUseCase,
    GetMovementUseCase,
    GetStockByPairUseCase,
    InboundMovementUseCase,
    ListMovementsUseCase,
    ListProductsUseCase,
    ListStocksUseCase,
    ListWarehousesUseCase,
    ReceiveMovementUseCase,
    TransferMovementUseCase,
    UpdateWarehouseUseCase,
)
from src.domain.interfaces import (
    IMovementRepository,
    ISkuRepository,
    IStockRepository,
    IUnitOfWork,
)
from src.infrastructure.db import async_session_factory
from src.infrastructure.uow import SqlAlchemyUnitOfWork


async def get_session() -> AsyncGenerator[AsyncSession]:
    async with async_session_factory() as session:
        yield session


async def get_uow(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AsyncGenerator[IUnitOfWork]:
    uow = SqlAlchemyUnitOfWork(session)
    async with uow:
        yield uow


def get_sku_repo(uow: Annotated[IUnitOfWork, Depends(get_uow)]) -> ISkuRepository:
    return uow.sku_repo


def get_stock_repo(uow: Annotated[IUnitOfWork, Depends(get_uow)]) -> IStockRepository:
    return uow.stock_repo


def get_movement_repo(uow: Annotated[IUnitOfWork, Depends(get_uow)]) -> IMovementRepository:
    return uow.movement_repo


def get_list_products_use_case(
    uow: Annotated[IUnitOfWork, Depends(get_uow)],
) -> ListProductsUseCase:
    return ListProductsUseCase(uow=uow)


def get_create_product_use_case(
    uow: Annotated[IUnitOfWork, Depends(get_uow)],
) -> CreateProductUseCase:
    return CreateProductUseCase(uow=uow)


def get_list_warehouses_use_case(
    uow: Annotated[IUnitOfWork, Depends(get_uow)],
) -> ListWarehousesUseCase:
    return ListWarehousesUseCase(uow=uow)


def get_list_stocks_use_case(
    uow: Annotated[IUnitOfWork, Depends(get_uow)],
) -> ListStocksUseCase:
    return ListStocksUseCase(uow=uow)


def get_stock_by_pair_use_case(
    uow: Annotated[IUnitOfWork, Depends(get_uow)],
) -> GetStockByPairUseCase:
    return GetStockByPairUseCase(uow=uow)


def get_list_movements_use_case(
    uow: Annotated[IUnitOfWork, Depends(get_uow)],
) -> ListMovementsUseCase:
    return ListMovementsUseCase(uow=uow)


def get_movement_use_case(
    uow: Annotated[IUnitOfWork, Depends(get_uow)],
) -> GetMovementUseCase:
    return GetMovementUseCase(uow=uow)


def get_create_warehouse_use_case(
    uow: Annotated[IUnitOfWork, Depends(get_uow)],
) -> CreateWarehouseUseCase:
    return CreateWarehouseUseCase(uow=uow)


def get_update_warehouse_use_case(
    uow: Annotated[IUnitOfWork, Depends(get_uow)],
) -> UpdateWarehouseUseCase:
    return UpdateWarehouseUseCase(uow=uow)


def get_delete_warehouse_use_case(
    uow: Annotated[IUnitOfWork, Depends(get_uow)],
) -> DeleteWarehouseUseCase:
    return DeleteWarehouseUseCase(uow=uow)


def get_inbound_movement_use_case(
    uow: Annotated[IUnitOfWork, Depends(get_uow)],
) -> InboundMovementUseCase:
    return InboundMovementUseCase(uow=uow)


def get_transfer_movement_use_case(
    uow: Annotated[IUnitOfWork, Depends(get_uow)],
) -> TransferMovementUseCase:
    return TransferMovementUseCase(uow=uow)


def get_receive_movement_use_case(
    uow: Annotated[IUnitOfWork, Depends(get_uow)],
) -> ReceiveMovementUseCase:
    return ReceiveMovementUseCase(uow=uow)


def get_fbo_out_movement_use_case(
    uow: Annotated[IUnitOfWork, Depends(get_uow)],
) -> FboOutMovementUseCase:
    return FboOutMovementUseCase(uow=uow)


def get_fbo_receive_movement_use_case(
    uow: Annotated[IUnitOfWork, Depends(get_uow)],
) -> FboReceiveMovementUseCase:
    return FboReceiveMovementUseCase(uow=uow)


def get_fbs_reserve_movement_use_case(
    uow: Annotated[IUnitOfWork, Depends(get_uow)],
) -> FbsReserveMovementUseCase:
    return FbsReserveMovementUseCase(uow=uow)


def get_fbs_ship_movement_use_case(
    uow: Annotated[IUnitOfWork, Depends(get_uow)],
) -> FbsShipMovementUseCase:
    return FbsShipMovementUseCase(uow=uow)


def get_fbs_cancel_movement_use_case(
    uow: Annotated[IUnitOfWork, Depends(get_uow)],
) -> FbsCancelMovementUseCase:
    return FbsCancelMovementUseCase(uow=uow)
