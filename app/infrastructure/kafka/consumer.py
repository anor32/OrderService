import json

from aiokafka import AIOKafkaConsumer, ConsumerRecord

from app.core.config import KAFKA_BOOTSTRAP_SERVERS
from app.core.logs_config import api_logger
from app.core.schemas.dto import InboxDTO
from app.infrastructure.clients.capashino_services import (
    NotificationServiceImpl,
)
from app.infrastructure.db.db_config import AsyncSession
from app.infrastructure.db.repository import (
    InboxRepositoryImpl,
    OrderRepositoryImpl,
)
from app.infrastructure.db.unit_of_work import UnitOfWorkConsumerImpl


class KafkaConsumer:
    def __init__(self):
        api_logger.info("ee1e")
        self.consumer = self.create_consumer()
        self.order_processor = None

    async def init_services(self, session: AsyncSession):
        order_repo = OrderRepositoryImpl(session)
        inbox_repo = InboxRepositoryImpl(session)
        self.uow = UnitOfWorkConsumerImpl(order_repo, session, inbox_repo)
        self.notify = NotificationServiceImpl()

    def create_consumer(self):
        self.consumer = AIOKafkaConsumer(
            "student_system-shipment.events",
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id="order_processors",
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            max_poll_records=50,
        )
        return self.consumer

    async def start(self):
        await self.consumer.start()

    async def stop(self):
        if self.consumer:
            await self.consumer.stop()

    async def _handle_message(self, msg: ConsumerRecord):
        self.event_data = msg.value
        if not isinstance(self.event_data, dict):
            return True
        self.order_id = self.event_data.get("order_id")
        self.idempotency_key = str(self.order_id)
        if not self.order_id:
            return True

    async def _save_to_inbox(self):
        async with AsyncSession() as session:
            await self.init_services(session)
            async with self.uow as u:
                inbox = await u.inbox_repo.get_by_idempotency_key(
                    self.idempotency_key
                )
                if inbox:
                    return inbox
                inbox_dto = InboxDTO(
                    idempotency_key=self.idempotency_key,
                    payload=self.event_data,
                    result={},
                )
                api_logger.info("получен order_id %s", self.order_id)
                api_logger.info(inbox_dto)
                await u.inbox_repo.save(inbox_dto)
                await u.commit()
                api_logger.info("save")

    async def consume(self):
        await self.start()
        api_logger.info("consumer слушает")

        async for msg in self.consumer:
            try:
                error = await self._handle_message(msg)
                if error:
                    continue
                await self._save_to_inbox()

            except Exception as e:
                api_logger.error("сonsumer Error %s", e)
                continue

    api_logger.info("сonsumer не слушает")
