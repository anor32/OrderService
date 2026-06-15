from abc import ABC, abstractmethod
from typing import Any, Self
from uuid import UUID

from app.core.schemas.dto import InboxDTO, OrderCreateDTO, OutboxDTO
from app.core.schemas.entities import (
    CatalogResponse,
    CreatePaymentRequest,
    InboxEvent,
    Order,
    OrderEvent,
    Outbox,
)
from app.core.schemas.statuses import OrderStatus


class OrderRepository(ABC):
    @abstractmethod
    async def create(self, order: OrderCreateDTO) -> Order:
        pass

    @abstractmethod
    async def get_by_id(self, order_id: str) -> Order | None:
        pass

    @abstractmethod
    async def set_order_status(self, status: OrderStatus, order_id: str):
        pass


class OutboxRepository(ABC):
    @abstractmethod
    async def create_outbox(self, outbox: OutboxDTO) -> Outbox:
        pass

    @abstractmethod
    async def get_records(self) -> list[Outbox]:
        pass

    @abstractmethod
    async def set_sent_status(self, ids: list[str]) -> None:
        pass


class InboxRepository(ABC):
    @abstractmethod
    async def get_by_idempotency_key(self, key: str) -> InboxEvent | None:
        pass

    @abstractmethod
    async def get_pending(self, limit: int = 100) -> list[InboxEvent]:
        pass

    @abstractmethod
    async def save(self, dto: InboxDTO) -> None:
        pass

    @abstractmethod
    async def check_idempotency(
        self, key: UUID, payload: dict[str, Any]
    ) -> None:
        pass


class UnitOfWorkBase(ABC):
    @abstractmethod
    async def __aenter__(self) -> Self:
        pass

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    @abstractmethod
    async def commit(self):
        pass

    @abstractmethod
    async def rollback(self):
        pass

    @abstractmethod
    async def close(self):
        pass


class CatalogService(ABC):
    @abstractmethod
    async def check_item(self, item_id: UUID) -> CatalogResponse:
        pass


class PaymentService(ABC):
    @abstractmethod
    async def create_payment(self, body: CreatePaymentRequest) -> None:
        pass


class UnitOfWorkOrders(UnitOfWorkBase):
    outbox_repo: OutboxRepository
    order_repo: OrderRepository
    inbox_repo: InboxRepository


class UnitOfWorkOutbox(UnitOfWorkBase):
    outbox_repo: OutboxRepository


class UnitOfWorkConsumer(UnitOfWorkBase):
    order_repo: OrderRepository


class ShippingService(ABC):
    @abstractmethod
    async def sent_to_service(self, order: OrderEvent):
        pass
