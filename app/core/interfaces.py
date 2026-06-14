from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Self
from uuid import UUID

from pydantic import BaseModel

from app.core.schemas import (
    CatalogResponse,
    InboxEvent,
    Order,
    Outbox,
    OutboxStatus,
)


class OrderRepository(ABC):
    class CreateDTO(BaseModel):
        user_id: str
        item_id: UUID
        quantity: int

    @abstractmethod
    async def create(self, order: CreateDTO) -> Order:
        pass

    @abstractmethod
    async def get_by_id(self, order_id: str) -> Order | None:
        pass


class OutboxRepository(ABC):
    class CreateDTO(BaseModel):
        event_type: str
        status: OutboxStatus
        payload: dict
        created_at: datetime

    @abstractmethod
    async def create_outbox(self, outbox: CreateDTO) -> Outbox:
        pass

    @abstractmethod
    async def get_records(self) -> list[Outbox]:
        pass

    @abstractmethod
    async def set_sent_status(self, ids: list[UUID]) -> None:
        pass


class InboxRepository(ABC):
    class CreateDTO(BaseModel):
        idempotency_key: str
        payload: dict[str, Any]
        result: dict[str, Any]

    @abstractmethod
    async def get_by_idempotency_key(self, key: str) -> InboxEvent | None:
        pass

    @abstractmethod
    async def get_pending(self, limit: int = 100) -> list[InboxEvent]:
        pass

    @abstractmethod
    async def save(self, dto: CreateDTO) -> None:
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


class UnitOfWork(UnitOfWorkBase):
    outbox_repo: OutboxRepository
    order_repo: OrderRepository
    inbox_repo: InboxRepository
