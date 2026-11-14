from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from src.api.dependencies import (
    get_create_warehouse_use_case,
    get_delete_warehouse_use_case,
    get_list_warehouses_use_case,
    get_update_warehouse_use_case,
)
from src.api.schemas import (
    ListWarehousesRequest,
    WarehouseCreateRequest,
    WarehouseResponse,
    WarehouseUpdateRequest,
)
from src.application.dtos import CreateWarehouseDTO, ListWarehousesDTO, UpdateWarehouseInput
from src.application.usecases import (
    CreateWarehouseUseCase,
    DeleteWarehouseUseCase,
    ListWarehousesUseCase,
    UpdateWarehouseUseCase,
)

router = APIRouter(prefix="/api/v1", tags=["warehouses"])


@router.get("/warehouses", response_model=list[WarehouseResponse])
async def list_warehouses(
    uc: Annotated[ListWarehousesUseCase, Depends(get_list_warehouses_use_case)],
    payload: Annotated[ListWarehousesRequest, Query()],
) -> list[WarehouseResponse]:
    query = ListWarehousesDTO(**payload.model_dump())
    warehouses = await uc.execute(query)
    return [WarehouseResponse.model_validate(w) for w in warehouses]


@router.post("/warehouses", response_model=WarehouseResponse, status_code=status.HTTP_201_CREATED)
async def create_warehouse(
    payload: WarehouseCreateRequest,
    uc: Annotated[CreateWarehouseUseCase, Depends(get_create_warehouse_use_case)],
) -> WarehouseResponse:
    input_dto = CreateWarehouseDTO(**payload.model_dump())
    warehouse = await uc.execute(input_dto)
    return WarehouseResponse.model_validate(warehouse)


@router.patch("/warehouses/{warehouse_id}", response_model=WarehouseResponse)
async def update_warehouse(
    warehouse_id: int,
    payload: WarehouseUpdateRequest,
    uc: Annotated[UpdateWarehouseUseCase, Depends(get_update_warehouse_use_case)],
) -> WarehouseResponse:
    warehouse = await uc.execute(UpdateWarehouseInput(warehouse_id=warehouse_id, name=payload.name))
    return WarehouseResponse.model_validate(warehouse)


@router.delete("/warehouses/{warehouse_id}", response_model=WarehouseResponse)
async def delete_warehouse(
    warehouse_id: int,
    uc: Annotated[DeleteWarehouseUseCase, Depends(get_delete_warehouse_use_case)],
) -> WarehouseResponse:
    warehouse = await uc.execute(warehouse_id)
    return WarehouseResponse.model_validate(warehouse)
