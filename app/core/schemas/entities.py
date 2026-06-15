import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.domain_exceptions import NotEnoughStockError
from app.core.schemas.dto import InboxDTO, OrderCreateDTO, OutboxDTO
from app.core.schemas.statuses import (
    InboxStatus,
    OrderStatus,
    OutboxStatus,
    PaymentStatus,
)


class PaymentResponse(BaseModel):
    payment_id: UUID
    order_id: UUID
    amount: Decimal
    status: PaymentStatus
    error_message: str | None

    def check_status(self) -> OrderStatus:
        if self.status == PaymentStatus.SUCCEEDED:
            db_status = OrderStatus.PAID
        else:
            db_status = OrderStatus.CANCELLED
        return db_status


class OrderEvent(BaseModel):
    event_type: OrderStatus
    order_id: UUID
    item_id: UUID
    quantity: int
    idempotency_key: UUID

    def to_payload(self) -> dict:
        return {
            "event_type": self.event_type,
            "order_id": str(self.order_id),
            "item_id": str(self.item_id),
            "quantity": self.quantity,
            "idempotency_key": str(self.idempotency_key),
        }

    def to_outbox_dto(self) -> OutboxDTO:
        return OutboxDTO(
            event_type=self.event_type,
            payload=self.to_payload(),
            status=OutboxStatus.PENDING,
            created_at=datetime.now(),
        )


class Order(BaseModel):
    id: UUID
    user_id: str
    item_id: UUID
    quantity: int
    status: OrderStatus = Field(default=OrderStatus.NEW)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime | None = None

    def to_order_event(self, payment: PaymentResponse) -> OrderEvent:
        return OrderEvent(
            event_type=payment.check_status(),
            order_id=self.id,
            quantity=self.quantity,
            idempotency_key=payment.payment_id,
            item_id=self.item_id,
        )


class CreateOrderRequest(BaseModel):
    user_id: str
    item_id: UUID
    quantity: int
    idempotency_key: str

    def to_order_dto(self) -> OrderCreateDTO:
        return OrderCreateDTO(
            user_id=self.user_id,
            item_id=self.item_id,
            quantity=self.quantity,
        )

    def to_inbox_dto(self, created_order: Order) -> InboxDTO:
        return InboxDTO(
            idempotency_key=self.idempotency_key,
            payload=self.model_dump(mode="json"),
            result=created_order.model_dump(mode="json"),
        )


class OrderResponse(BaseModel):
    id: UUID
    user_id: str
    item_id: UUID
    quantity: int
    status: OrderStatus
    created_at: datetime
    updated_at: datetime


class Payment(BaseModel):
    payment_id: UUID = Field(default_factory=uuid.uuid4)
    order_id: UUID
    status: PaymentStatus
    amount: Decimal
    error_message: str | None


class Outbox(BaseModel):
    id: UUID = Field(default_factory=uuid.uuid4)
    event_type: str
    status: OutboxStatus = Field(default=OutboxStatus.PENDING)
    payload: dict
    created_at: datetime = Field(default_factory=datetime.now)
    sent_at: datetime | None = None


class InboxEvent(BaseModel):
    idempotency_key: UUID | str
    status: InboxStatus
    payload: dict[str, Any]
    result: dict[str, Any]
    created_at: datetime | None = None
    processed_at: datetime | None = None


class CatalogResponse(BaseModel):
    id: UUID
    name: str
    price: str
    available_qty: int
    created_at: datetime

    def is_available(self, quantity: int) -> bool:
        if self.available_qty >= quantity:
            return True
        raise NotEnoughStockError("Товара нет в наличии")


class CreatePaymentRequest(BaseModel):
    order_id: UUID
    amount: Decimal
    callback_url: str
    idempotency_key: str
