"""Stock v1 routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from src.api.dependencies import get_list_stocks_use_case, get_stock_by_pair_use_case
from src.api.schemas import (
    ListStocksRequest,
    PaginatedStocksResponse,
    StockItemResponse,
)
from src.application.dtos import ListStocksQuery
from src.application.pagination import Pagination
from src.application.usecases import GetStockByPairUseCase, ListStocksUseCase

router = APIRouter(prefix="/api/v1", tags=["stocks"])


@router.get("/stocks", response_model=PaginatedStocksResponse)
async def list_stocks(
    uc: Annotated[ListStocksUseCase, Depends(get_list_stocks_use_case)],
    payload: Annotated[ListStocksRequest, Query()],
) -> PaginatedStocksResponse:
    query = ListStocksQuery(
        pagination=Pagination(page=payload.page, page_size=payload.page_size),
        sku=payload.sku,
        warehouse_id=payload.warehouse_id,
        include_deleted_warehouses=payload.include_deleted_warehouses,
    )
    result = await uc.execute(query)
    return PaginatedStocksResponse(
        items=[StockItemResponse.model_validate(i) for i in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


@router.get("/stocks/{product_id}/{warehouse_id}", response_model=StockItemResponse)
async def get_stock_by_pair(
    product_id: int,
    warehouse_id: int,
    uc: Annotated[GetStockByPairUseCase, Depends(get_stock_by_pair_use_case)],
) -> StockItemResponse:
    item = await uc.execute(product_id=product_id, warehouse_id=warehouse_id)
    return StockItemResponse.model_validate(item)
