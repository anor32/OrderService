import json
from uuid import UUID

from aiokafka import AIOKafkaConsumer

from app.application.processors import OrderProcessor
from app.core.config import KAFKA_BOOTSTRAP_SERVERS
from app.core.logs_config import api_logger
from app.core.schemas.entities import NotificationBody
from app.core.schemas.statuses import OrderStatus
from app.infrastructure.clients.capashino_services import (
    NotificationServiceImpl,
)
from app.infrastructure.db.db_config import AsyncSession
from app.infrastructure.db.repository import OrderRepositoryImpl
from app.infrastructure.db.unit_of_work import UnitOfWorkConsumerImpl


class KafkaConsumer:
    def __init__(self):
        self.consumer = None
        self.order_processor = None

    async def init_consumer(self):
        api_logger.info("инициализация consumer")
        self._session = AsyncSession()
        order_repo = OrderRepositoryImpl(self._session)
        uow = UnitOfWorkConsumerImpl(order_repo, self._session)
        self.order_processor = OrderProcessor(uow)
        self.notify = NotificationServiceImpl()
        try:
            await self.start()
        except Exception as e:
            api_logger.error("Ошибка инциализации сonsumer %s", e)
            return False
        else:
            return True

    async def create_consumer(self):
        self.consumer = AIOKafkaConsumer(
            "student_system-shipment.events",
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id="order_processors",
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        )
        return self.consumer

    async def start(self):
        if self.consumer is None:
            await self.create_consumer()
        await self.consumer.start()

    async def stop(self):
        if self.consumer:
            await self.consumer.stop()

    async def consume(self):
        await self.init_consumer()
        api_logger.info("consumer слушает")
        async for msg in self.consumer:
            event_data = msg.value
            event_type = event_data.get("event_type")
            order_id = event_data.get("order_id")

            if not order_id:
                continue
            api_logger.info("получен order_id %s", order_id)
            if event_type == "order.shipped":
                status = OrderStatus.SHIPPED
                message = "Order is shipped"

            elif event_type == "order.cancelled":
                status = OrderStatus.CANCELLED
                message = "order is cancelled"
            else:
                continue
            try:
                await self.order_processor.process_shipping_callback(
                    status, UUID(order_id)
                )
                api_logger.info("отправка уведомления косюмер")
                notify_body = NotificationBody(
                    message=message,
                    reference_id=str(order_id),
                    idempotency_key=str(order_id),
                )
                await self.notify.send_notification(notify_body)
            except Exception as e:
                api_logger.error("сonsumer Error %s", e)
                continue
            api_logger.info("сonsumer не слушает")
