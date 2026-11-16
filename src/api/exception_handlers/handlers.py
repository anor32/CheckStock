from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from src.api.schemas import ErrorResponse
from src.domain.exceptions import (
    CheckStockDomainError,
    EntityNotFoundError,
    InsufficientStockError,
    InvalidMovementError,
    ProductAlreadyExistsError,
    ProductNotFoundError,
    WarehouseDeletedError,
    WarehouseHasActiveMovementsError,
)


async def entity_not_found_handler(_: Request, exc: EntityNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


async def product_not_found_handler(_: Request, exc: ProductNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


async def insufficient_stock_handler(_: Request, exc: InsufficientStockError) -> JSONResponse:
    payload = exc.info if exc.info is not None else exc.data
    response = ErrorResponse.from_error_data(payload)
    return JSONResponse(status_code=409, content=response.model_dump())


async def invalid_movement_handler(_: Request, exc: InvalidMovementError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


async def warehouse_deleted_handler(_: Request, exc: WarehouseDeletedError) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exc)})


async def warehouse_has_active_movements_handler(
    _: Request, exc: WarehouseHasActiveMovementsError
) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exc)})


async def product_already_exists_handler(
    _: Request, exc: ProductAlreadyExistsError
) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exc)})


async def checkstock_domain_error_handler(_: Request, exc: CheckStockDomainError) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exc)})


async def integrity_error_handler(_: Request, exc: IntegrityError) -> JSONResponse:
    message = str(getattr(exc, "orig", exc))
    if "ck_stock_reserved_le_physical" in message:
        return JSONResponse(
            status_code=409,
            content={
                "detail": "Недостаточно доступного остатка: операция нарушает ограничение резерва (FBS) и физического остатка."
            },
        )
    return JSONResponse(status_code=409, content={"detail": "Нарушение целостности данных."})


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(EntityNotFoundError, entity_not_found_handler)
    app.add_exception_handler(ProductNotFoundError, product_not_found_handler)
    app.add_exception_handler(InsufficientStockError, insufficient_stock_handler)
    app.add_exception_handler(InvalidMovementError, invalid_movement_handler)
    app.add_exception_handler(WarehouseDeletedError, warehouse_deleted_handler)
    app.add_exception_handler(
        WarehouseHasActiveMovementsError, warehouse_has_active_movements_handler
    )
    app.add_exception_handler(ProductAlreadyExistsError, product_already_exists_handler)
    app.add_exception_handler(CheckStockDomainError, checkstock_domain_error_handler)
    app.add_exception_handler(IntegrityError, integrity_error_handler)
