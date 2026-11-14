"""Product v1 routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.api.dependencies import get_create_product_use_case, get_list_products_use_case
from src.api.schemas import ProductCreateRequest, ProductResponse
from src.application.dtos import CreateProductDTO
from src.application.usecases import CreateProductUseCase, ListProductsUseCase

router = APIRouter(prefix="/api/v1", tags=["products"])


@router.get("/products", response_model=list[ProductResponse])
async def list_products(
    uc: Annotated[ListProductsUseCase, Depends(get_list_products_use_case)],
) -> list[ProductResponse]:
    products = await uc.execute()
    return [ProductResponse.model_validate(p) for p in products]


@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreateRequest,
    uc: Annotated[CreateProductUseCase, Depends(get_create_product_use_case)],
) -> ProductResponse:
    input_dto = CreateProductDTO(**payload.model_dump())
    product = await uc.execute(input_dto)
    return ProductResponse.model_validate(product)
