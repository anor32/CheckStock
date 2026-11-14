"""Product v1 routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.api.dependencies import get_create_product_use_case, get_list_products_use_case
from src.api.schemas import ProductCreateRequest, ProductResponse
from src.application.dtos import CreateProductInput
from src.application.usecases import CreateProductUseCase, ListProductsUseCase

router = APIRouter(prefix="/api/v1", tags=["products"])


@router.get("/products", response_model=list[ProductResponse])
async def list_products(
    uc: Annotated[ListProductsUseCase, Depends(get_list_products_use_case)],
) -> list[ProductResponse]:
    items = await uc.execute()
    return [
        ProductResponse(id=i.id, sku=i.sku, name=i.name, idempotency_key=i.idempotency_key)
        for i in items
    ]


@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreateRequest,
    uc: Annotated[CreateProductUseCase, Depends(get_create_product_use_case)],
) -> ProductResponse:
    item = await uc.execute(
        CreateProductInput(
            sku=payload.sku, name=payload.name, idempotency_key=payload.idempotency_key
        )
    )
    return ProductResponse(
        id=item.id, sku=item.sku, name=item.name, idempotency_key=item.idempotency_key
    )
