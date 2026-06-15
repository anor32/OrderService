from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from app.core.schemas.statuses import OutboxStatus


class InboxDTO(BaseModel):
    idempotency_key: str
    payload: dict[str, Any]
    result: dict[str, Any]


class OutboxDTO(BaseModel):
    event_type: str
    payload: dict[str, Any]
    status: OutboxStatus
    created_at: datetime


class OrderCreateDTO(BaseModel):
    user_id: str
    item_id: UUID
    quantity: int


class OrderUpdateDTO(BaseModel):
    order_id: UUID
    status: str
    updated_at: datetime = datetime.now()
