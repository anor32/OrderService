from abc import ABC, abstractmethod
from datetime import datetime
from typing import Self
from uuid import UUID

from pydantic import BaseModel

from app.core.schemas import Order, Outbox, OutboxStatus


class OrderRepository(ABC):
    class CreateDTO(BaseModel):
        user_id: str
        item_id: UUID
        quantity: int

    @abstractmethod
    def create(self, order: CreateDTO) -> None:
        pass

    @abstractmethod
    def get_by_id(self, order_id: str) -> Order | None:
        pass


class OutboxRepository(ABC):
    class CreateDTO(BaseModel):
        event_type: str
        status: OutboxStatus
        payload: dict
        created_at: datetime

    @abstractmethod
    async def create_outbox(self, outbox: CreateDTO):
        pass

    @abstractmethod
    async def get_records(self) -> list[Outbox]:
        pass

    @abstractmethod
    async def set_sent_status(self, ids: list[UUID]) -> None:
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


class UnitOfWork(UnitOfWorkBase):
    outbox_repo: OutboxRepository
    order_repo: OrderRepository
