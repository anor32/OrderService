from typing import Any

from app.core.interfaces import NotificationService, UnitOfWorkConsumer
from app.core.logs_config import api_logger
from app.core.schemas.entities import NotificationBody
from app.core.schemas.statuses import OrderStatus


class OrderProcessor:
    def __init__(
        self,
        uow: UnitOfWorkConsumer,
        notification_service: NotificationService,
    ):
        self.uow = uow
        self.notify = notification_service

    async def check_inbox(self, key: str) -> None | dict[str, Any]:
        async with self.uow as uow:
            inbox = await uow.inbox_repo.get_by_idempotency_key(key)
        if inbox:
            return inbox.result

    async def process_messages_in_inbox(
        self, status: OrderStatus, order_id: str
    ):
        api_logger.info("обновление статуса")
        await self.uow.order_repo.set_order_status(status, str(order_id))

    async def sent_notify(self, notify_body: NotificationBody):
        await self.notify.send_notification(notify_body)
