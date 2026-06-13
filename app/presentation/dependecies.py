from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services import OrderService
from app.core.interfaces import UnitOfWork
from app.infrastructure.db.db_config import AsyncSession as AsyncSessionFactory
from app.infrastructure.db.repository import (
    InboxRepositoryImpl,
    OrderRepositoryImpl,
    OutboxRepositoryImpl,
)
from app.infrastructure.db.unit_of_work import UnitOfWorkOrders


async def get_db():
    db = AsyncSessionFactory()
    try:
        yield db
    finally:
        await db.close()


def get_uow(session: Annotated[AsyncSession, Depends(get_db)]) -> UnitOfWork:
    order_repo = OrderRepositoryImpl(session)
    outbox_repo = OutboxRepositoryImpl(session)
    inbox_repo = InboxRepositoryImpl(session)

    return UnitOfWorkOrders(
        session=session,
        order_repo=order_repo,
        outbox_repo=outbox_repo,
        inbox_repo=inbox_repo,
    )


def get_order_service(
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> OrderService:
    return OrderService(uow=uow)


DepOrderService = Annotated[OrderService, Depends(get_order_service)]
