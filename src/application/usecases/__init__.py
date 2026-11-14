"""Use cases package."""

from src.application.usecases.movements import (
    FboOutMovementUseCase,
    FboReceiveMovementUseCase,
    FbsCancelMovementUseCase,
    FbsReserveMovementUseCase,
    FbsShipMovementUseCase,
    GetMovementUseCase,
    InboundMovementUseCase,
    ListMovementsUseCase,
    ReceiveMovementUseCase,
    TransferMovementUseCase,
)
from src.application.usecases.products import CreateProductUseCase, ListProductsUseCase
from src.application.usecases.stocks import GetStockByPairUseCase, ListStocksUseCase
from src.application.usecases.warehouses import (
    CreateWarehouseUseCase,
    DeleteWarehouseUseCase,
    ListWarehousesUseCase,
    UpdateWarehouseUseCase,
)

__all__ = [
    "CreateProductUseCase",
    "CreateWarehouseUseCase",
    "DeleteWarehouseUseCase",
    "FboOutMovementUseCase",
    "FboReceiveMovementUseCase",
    "FbsCancelMovementUseCase",
    "FbsReserveMovementUseCase",
    "FbsShipMovementUseCase",
    "GetMovementUseCase",
    "GetStockByPairUseCase",
    "InboundMovementUseCase",
    "ListMovementsUseCase",
    "ListProductsUseCase",
    "ListStocksUseCase",
    "ListWarehousesUseCase",
    "ReceiveMovementUseCase",
    "TransferMovementUseCase",
    "UpdateWarehouseUseCase",
]
