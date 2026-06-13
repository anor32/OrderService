from abc import ABC, abstractmethod
from uuid import UUID

from pydantic import BaseModel

from app.core.schemas import Order


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
    @abstractmethod
    def create_outbox(self, outbox):
        pass

    @abstractmethod
    def get_records(self):
        pass

    @abstractmethod
    def set_sent_status(self):
        pass


class UnitOfWorkBase(ABC):
    @abstractmethod
    async def __aenter__(self):
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
