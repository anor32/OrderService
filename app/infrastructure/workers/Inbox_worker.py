import asyncio

from app.application.processors import OrderProcessor
from app.core.logs_config import api_logger
from app.core.schemas.entities import NotificationBody
from app.core.schemas.statuses import OrderStatus
from app.infrastructure.clients.capashino_services import (
    NotificationServiceImpl,
)
from app.infrastructure.db.db_config import AsyncSession
from app.infrastructure.db.repository import (
    InboxRepositoryImpl,
    OrderRepositoryImpl,
)
from app.infrastructure.db.unit_of_work import UnitOfWorkConsumerImpl


class InboxWorker:
    async def _init_uow(self):
        session = AsyncSession()
        inbox_repo = InboxRepositoryImpl(session)
        order_repo = OrderRepositoryImpl(session)
        uow = UnitOfWorkConsumerImpl(
            session=session, inbox_repo=inbox_repo, order_repo=order_repo
        )
        self.notify = NotificationServiceImpl()
        self._ord_proc = OrderProcessor(
            uow=uow, notification_service=self.notify
        )
        return uow

    async def process(self, limit: int = 100):
        uow = await self._init_uow()
        async with uow as u:
            pending = await u.inbox_repo.get_pending(limit)
            ids = []
            notifies = []
            api_logger.info("pending %s", pending)
            for record in pending:
                event_data = record.payload

                event_type = event_data.get("event_type")
                order_id = event_data.get("order_id")
                if event_type == "order.shipped":
                    status = OrderStatus.SHIPPED
                    api_logger.info("not skip")
                    message = "Order is shipped"

                elif event_type == "order.cancelled":
                    status = OrderStatus.CANCELLED
                    api_logger.info("not skip")
                    message = "order is cancelled"
                else:
                    id = record.idempotency_key
                    ids.append(id)
                    continue

                notify_body = NotificationBody(
                    message=message,
                    reference_id=str(order_id),
                    idempotency_key=record.idempotency_key,
                )
                notifies.append(notify_body)

                await self._ord_proc.process_messages_in_inbox(
                    status, str(order_id)
                )
                ids.append(record.idempotency_key)

            await u.inbox_repo.set_status_processed(ids=ids)
        for notify_body in notifies:
            await self._ord_proc.sent_notify(notify_body)

    async def work(self, delay: int = 60, limit: int = 100):
        api_logger.info(
            "InboxWorker запущен, проверка каждые %s секунд", delay
        )

        while True:
            try:
                await self.process(limit=limit)
            except Exception as e:
                api_logger.error(
                    "InboxWorker: критическая ошибка в цикле: %s", e
                )

            await asyncio.sleep(delay)
