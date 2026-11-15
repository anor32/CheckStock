"""Movement v1 routes."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from src.api.dependencies import (
    get_fbo_out_movement_use_case,
    get_fbo_receive_movement_use_case,
    get_fbs_cancel_movement_use_case,
    get_fbs_reserve_movement_use_case,
    get_fbs_ship_movement_use_case,
    get_inbound_movement_use_case,
    get_list_movements_use_case,
    get_movement_use_case,
    get_receive_movement_use_case,
    get_transfer_movement_use_case,
)
from src.api.schemas import (
    FboOutMovementRequest,
    FboReceiveMovementRequest,
    FbsCancelMovementRequest,
    FbsReserveMovementRequest,
    FbsShipMovementRequest,
    InboundMovementRequest,
    ListMovementsRequest,
    MovementResponse,
    PaginatedMovementsResponse,
    ReceiveMovementRequest,
    TransferMovementRequest,
)
from src.application.dtos import (
    CreateFboOutMovementInput,
    CreateFbsReserveMovementInput,
    CreateInboundMovementInput,
    CreateTransferMovementInput,
    FboReceiveMovementInput,
    FbsCancelMovementInput,
    FbsShipMovementInput,
    ListMovementsDTO,
    ReceiveMovementInput,
)
from src.application.pagination import Pagination
from src.application.usecases import (
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

router = APIRouter(prefix="/api/v1", tags=["movements"])


@router.get("/movements", response_model=PaginatedMovementsResponse)
async def list_movements(
    uc: Annotated[ListMovementsUseCase, Depends(get_list_movements_use_case)],
    payload: Annotated[ListMovementsRequest, Query()],
) -> PaginatedMovementsResponse:
    date_from = datetime.fromisoformat(payload.date_from) if payload.date_from else None
    date_to = datetime.fromisoformat(payload.date_to) if payload.date_to else None
    query = ListMovementsDTO(
        pagination=Pagination(page=payload.page, page_size=payload.page_size),
        product_id=payload.product_id,
        movement_type=payload.movement_type,
        status=payload.status,
        warehouse_id=payload.warehouse_id,
        date_from=date_from,
        date_to=date_to,
    )
    result = await uc.execute(query)
    return PaginatedMovementsResponse(
        items=[MovementResponse.model_validate(i) for i in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


@router.get("/movements/{movement_id}", response_model=MovementResponse)
async def get_movement(
    movement_id: int,
    uc: Annotated[GetMovementUseCase, Depends(get_movement_use_case)],
) -> MovementResponse:
    movement = await uc.execute(movement_id)
    return MovementResponse.model_validate(movement)


@router.post(
    "/movements/inbound", response_model=MovementResponse, status_code=status.HTTP_201_CREATED
)
async def inbound_movement(
    payload: InboundMovementRequest,
    uc: Annotated[InboundMovementUseCase, Depends(get_inbound_movement_use_case)],
) -> MovementResponse:
    input_dto = CreateInboundMovementInput(**payload.model_dump())
    movement = await uc.execute(input_dto)
    return MovementResponse.model_validate(movement)


@router.post(
    "/movements/transfer", response_model=MovementResponse, status_code=status.HTTP_201_CREATED
)
async def transfer_movement(
    payload: TransferMovementRequest,
    uc: Annotated[TransferMovementUseCase, Depends(get_transfer_movement_use_case)],
) -> MovementResponse:
    input_dto = CreateTransferMovementInput(**payload.model_dump())
    movement = await uc.execute(input_dto)
    return MovementResponse.model_validate(movement)


@router.post("/movements/{movement_id}/receive", response_model=MovementResponse)
async def receive_movement(
    movement_id: int,
    uc: Annotated[ReceiveMovementUseCase, Depends(get_receive_movement_use_case)],
    payload: ReceiveMovementRequest | None = None,
) -> MovementResponse:
    input_dto = ReceiveMovementInput(
        movement_id=movement_id,
        idempotency_key=payload.idempotency_key if payload else None,
    )
    movement = await uc.execute(input_dto)
    return MovementResponse.model_validate(movement)


@router.post(
    "/movements/fbo-out", response_model=MovementResponse, status_code=status.HTTP_201_CREATED
)
async def fbo_out_movement(
    payload: FboOutMovementRequest,
    uc: Annotated[FboOutMovementUseCase, Depends(get_fbo_out_movement_use_case)],
) -> MovementResponse:
    input_dto = CreateFboOutMovementInput(**payload.model_dump())
    movement = await uc.execute(input_dto)
    return MovementResponse.model_validate(movement)


@router.post("/movements/{movement_id}/fbo-receive", response_model=MovementResponse)
async def fbo_receive_movement(
    movement_id: int,
    uc: Annotated[FboReceiveMovementUseCase, Depends(get_fbo_receive_movement_use_case)],
    payload: FboReceiveMovementRequest | None = None,
) -> MovementResponse:
    input_dto = FboReceiveMovementInput(
        movement_id=movement_id,
        idempotency_key=payload.idempotency_key if payload else None,
    )
    movement = await uc.execute(input_dto)
    return MovementResponse.model_validate(movement)


@router.post(
    "/movements/fbs-reserve", response_model=MovementResponse, status_code=status.HTTP_201_CREATED
)
async def fbs_reserve_movement(
    payload: FbsReserveMovementRequest,
    uc: Annotated[FbsReserveMovementUseCase, Depends(get_fbs_reserve_movement_use_case)],
) -> MovementResponse:
    input_dto = CreateFbsReserveMovementInput(**payload.model_dump())
    movement = await uc.execute(input_dto)
    return MovementResponse.model_validate(movement)


@router.post("/movements/{movement_id}/fbs-ship", response_model=MovementResponse)
async def fbs_ship_movement(
    movement_id: int,
    uc: Annotated[FbsShipMovementUseCase, Depends(get_fbs_ship_movement_use_case)],
    payload: FbsShipMovementRequest | None = None,
) -> MovementResponse:
    input_dto = FbsShipMovementInput(
        movement_id=movement_id,
        idempotency_key=payload.idempotency_key if payload else None,
    )
    movement = await uc.execute(input_dto)
    return MovementResponse.model_validate(movement)


@router.post("/movements/{movement_id}/fbs-cancel", response_model=MovementResponse)
async def fbs_cancel_movement(
    movement_id: int,
    uc: Annotated[FbsCancelMovementUseCase, Depends(get_fbs_cancel_movement_use_case)],
    payload: FbsCancelMovementRequest | None = None,
) -> MovementResponse:
    input_dto = FbsCancelMovementInput(
        movement_id=movement_id,
        idempotency_key=payload.idempotency_key if payload else None,
    )
    movement = await uc.execute(input_dto)
    return MovementResponse.model_validate(movement)
