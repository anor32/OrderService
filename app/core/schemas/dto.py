from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.schemas.statuses import InboxStatus, OutboxStatus


class InboxDTO(BaseModel):
    idempotency_key: str
    payload: dict[str, Any]
    result: dict[str, Any]
    status: InboxStatus = Field(default=InboxStatus.PENDING)


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
    updated_at: datetime = Field(default_factory=datetime.now)
