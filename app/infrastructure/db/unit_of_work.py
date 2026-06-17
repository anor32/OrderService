from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.interfaces import (
    InboxRepository,
    OrderRepository,
    OutboxRepository,
    UnitOfWorkConsumer,
    UnitOfWorkOrders,
    UnitOfWorkOutbox,
)


class BaseImplUnitOfWork:
    _session: AsyncSession

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            await self.commit()
        else:
            await self.rollback()
        await self.close()

    async def commit(self):
        await self._session.commit()

    async def close(self):
        await self._session.close()

    async def rollback(self):
        await self._session.rollback()


class UnitOfWorkOrdersImpl(BaseImplUnitOfWork, UnitOfWorkOrders):
    def __init__(
        self,
        session,
        order_repo: OrderRepository,
        outbox_repo: OutboxRepository,
        inbox_repo: InboxRepository,
    ):
        self._session = session
        self.order_repo = order_repo
        self.outbox_repo = outbox_repo
        self.inbox_repo = inbox_repo


class UnitOfWorkWorker(BaseImplUnitOfWork, UnitOfWorkOutbox):
    def __init__(self, outbox_repo: OutboxRepository, session: AsyncSession):
        self._session = session
        self.outbox_repo = outbox_repo


class UnitOfWorkConsumerImpl(BaseImplUnitOfWork, UnitOfWorkConsumer):
    def __init__(self, order_repo: OrderRepository, session: AsyncSession):
        self._session = session
        self.order_repo = order_repo
