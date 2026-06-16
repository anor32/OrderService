from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services import OrderService
from app.infrastructure.clients.capashino_services import (
    CatalogServiceImpl,
    PaymentServiceImpl,
)
from app.infrastructure.db.db_config import AsyncSession as AsyncSessionFactory
from app.infrastructure.db.repository import (
    InboxRepositoryImpl,
    OrderRepositoryImpl,
    OutboxRepositoryImpl,
)
from app.infrastructure.db.unit_of_work import (
    UnitOfWorkOrders,
    UnitOfWorkOrdersImpl,
)
from app.infrastructure.kafka.producer import KafkaProducer


async def get_db():
    db = AsyncSessionFactory()
    try:
        yield db
    finally:
        await db.close()


def get_uow(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> UnitOfWorkOrders:
    order_repo = OrderRepositoryImpl(session)
    outbox_repo = OutboxRepositoryImpl(session)
    inbox_repo = InboxRepositoryImpl(session)

    return UnitOfWorkOrdersImpl(
        session=session,
        order_repo=order_repo,
        outbox_repo=outbox_repo,
        inbox_repo=inbox_repo,
    )


catalog_client = CatalogServiceImpl()
payment = PaymentServiceImpl()
kafka = KafkaProducer()


def get_order_service(
    uow: Annotated[UnitOfWorkOrders, Depends(get_uow)],
) -> OrderService:
    return OrderService(
        uow=uow,
        catalog=catalog_client,
        payment_service=payment,
    )


DepOrderService = Annotated[OrderService, Depends(get_order_service)]
