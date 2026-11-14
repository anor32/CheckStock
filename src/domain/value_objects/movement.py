from __future__ import annotations

from enum import StrEnum


class MovementType(StrEnum):
    INBOUND = "inbound"
    TRANSFER_OUT = "transfer_out"
    TRANSFER_IN = "transfer_in"
    FBO_OUT = "fbo_out"
    FBO_RECEIVED = "fbo_received"
    FBS_RESERVE = "fbs_reserve"
    FBS_SHIP = "fbs_ship"
    FBS_CANCEL = "fbs_cancel"


class MovementStatus(StrEnum):
    PENDING = "pending"
    IN_TRANSIT = "in_transit"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
