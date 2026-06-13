from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel


class OrderStatus(StrEnum):
    NEW = "NEW"
    PAID = "PAID"
    SHIPPED = "SHIPPED"
    CANCELLED = "CANCELLED"


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


class PaymentStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class PaymentRequest(BaseModel):
    payment_id: UUID
    order_id: UUID
    status: PaymentStatus
    amount: Decimal
    error_message: str | None
