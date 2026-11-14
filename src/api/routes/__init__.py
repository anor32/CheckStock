"""API route modules."""

from src.api.routes.movement_routes import router as movement_router
from src.api.routes.product_routes import router as product_router
from src.api.routes.stock_routes import router as stock_router
from src.api.routes.warehouse_routes import router as warehouse_router

__all__ = [
    "movement_router",
    "product_router",
    "stock_router",
    "warehouse_router",
]
