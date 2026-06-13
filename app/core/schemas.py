from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class OutboxStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"


class InboxStatus(StrEnum):
    PENDING = "pending"
    PROCESSED = "processed"


class OrderStatus(StrEnum):
    NEW = "NEW"
    PAID = "PAID"
    SHIPPED = "SHIPPED"
    CANCELLED = "CANCELLED"


class PaymentStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class CreateOrderRequest(BaseModel):
    user_id: str
    item_id: UUID
    quantity: int
    idempotency_key: UUID


class Order(BaseModel):
    id: UUID
    user_id: str
    item_id: UUID
    quantity: int
    status: OrderStatus
    created_at: datetime
    updated_at: datetime


class OrderResponse(BaseModel):
    id: UUID
    user_id: str
    item_id: UUID
    quantity: int
    status: OrderStatus
    created_at: datetime
    updated_at: datetime


class PaymentRequest(BaseModel):
    payment_id: UUID
    order_id: UUID
    status: PaymentStatus
    amount: Decimal
    error_message: str | None


class Outbox(BaseModel):
    id: UUID
    event_type: str
    status: OutboxStatus = Field(default=OutboxStatus.PENDING)
    payload: dict
    created_at: datetime = Field(default_factory=datetime.now)
    sent_at: datetime | None = None


class InboxEvent(BaseModel):
    idempotency_key: UUID
    status: InboxStatus
    payload: dict[str, Any]
    result: dict[str, Any]
    created_at: datetime | None = None
    processed_at: datetime | None = None
