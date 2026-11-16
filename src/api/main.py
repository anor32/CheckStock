from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from src.api.routes import (
    movement_router,
    product_router,
    stock_router,
    warehouse_router,
)
from src.api.schemas import ErrorResponse
from src.domain.exceptions import (
    CheckStockDomainError,
    EntityNotFoundError,
    InsufficientStockError,
    InvalidMovementError,
    ProductAlreadyExistsError,
    ProductNotFoundError,
    WarehouseDeletedError,
)

app = FastAPI(title="CheckStock", version="0.1.0")

BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent.parent
STATIC_DIR = REPO_ROOT / "frontend"


@app.exception_handler(EntityNotFoundError)
async def entity_not_found_handler(_: Request, exc: EntityNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(ProductNotFoundError)
async def product_not_found_handler(_: Request, exc: ProductNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(InsufficientStockError)
async def insufficient_stock_handler(_: Request, exc: InsufficientStockError) -> JSONResponse:
    payload = exc.info if exc.info is not None else exc.data
    response = ErrorResponse.from_error_data(payload)
    return JSONResponse(status_code=409, content=response.model_dump())


@app.exception_handler(InvalidMovementError)
async def invalid_movement_handler(_: Request, exc: InvalidMovementError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(WarehouseDeletedError)
async def warehouse_deleted_handler(_: Request, exc: WarehouseDeletedError) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(ProductAlreadyExistsError)
async def product_already_exists_handler(
    _: Request, exc: ProductAlreadyExistsError
) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(CheckStockDomainError)
async def checkstock_domain_error_handler(_: Request, exc: CheckStockDomainError) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exc)})


app.include_router(product_router)
app.include_router(warehouse_router)
app.include_router(stock_router)
app.include_router(movement_router)


@app.get("/", include_in_schema=False)
async def serve_index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
