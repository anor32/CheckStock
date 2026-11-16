from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.api.exception_handlers import register_exception_handlers
from src.api.routes import (
    movement_router,
    product_router,
    stock_router,
    warehouse_router,
)

app = FastAPI(title="CheckStock", version="0.1.0")

BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent.parent
STATIC_DIR = REPO_ROOT / "frontend"

register_exception_handlers(app)

app.include_router(product_router)
app.include_router(warehouse_router)
app.include_router(stock_router)
app.include_router(movement_router)


@app.get("/", include_in_schema=False)
async def serve_index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
