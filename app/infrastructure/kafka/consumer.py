import json

from aiokafka import AIOKafkaConsumer, ConsumerRecord

from app.core.config import KAFKA_BOOTSTRAP_SERVERS
from app.core.logs_config import api_logger
from app.core.schemas.dto import InboxDTO
from app.infrastructure.db.db_config import AsyncSession
from app.infrastructure.db.repository import (
    InboxRepositoryImpl,
    OrderRepositoryImpl,
)
from app.infrastructure.db.unit_of_work import UnitOfWorkConsumerImpl


class KafkaConsumer:
    def __init__(self):
        self.consumer = self.create_consumer()
        self.uow = None

    async def init_services(self, session: AsyncSession):
        order_repo = OrderRepositoryImpl(session)
        inbox_repo = InboxRepositoryImpl(session)
        self.uow = UnitOfWorkConsumerImpl(order_repo, session, inbox_repo)

    def create_consumer(self):
        return AIOKafkaConsumer(
            "student_system-shipment.events",
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id="order_processors",
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            max_poll_records=50,
            max_poll_interval_ms=600000,
            session_timeout_ms=60000,
        )

    async def start(self):
        await self.consumer.start()

    async def stop(self):
        if self.consumer:
            await self.consumer.stop()

    async def _handle_message(self, msg: ConsumerRecord):
        event_data = msg.value
        api_logger.info("hear")

        if not isinstance(event_data, dict):
            return None, None, None

        ev_type = event_data.get("event_type")
        if ev_type not in ("order.shipped", "order.cancelled"):
            return None, None, None

        order_id = event_data.get("order_id")
        if not order_id:
            return None, None, None

        return event_data, order_id, str(order_id)

    async def _save_to_inbox(
        self, event_data: dict, order_id: str, idempotency_key: str
    ):
        async with AsyncSession() as session:
            api_logger.info("saving")
            await self.init_services(session)

            async with self.uow as u:
                inbox = await u.inbox_repo.get_by_idempotency_key(
                    idempotency_key
                )
                api_logger.info("transact")
                if inbox:
                    api_logger.info("Дубликат %s, пропускаем", idempotency_key)
                    return

                inbox_dto = InboxDTO(
                    idempotency_key=idempotency_key,
                    payload=event_data,
                    result={"success": True},
                )
                api_logger.info("получен order_id %s", order_id)
                api_logger.info(inbox_dto)
                await u.inbox_repo.save(inbox_dto)
                await u.commit()
                api_logger.info("save")

    async def consume(self):
        await self.start()
        api_logger.info("consumer слушает")

        async for msg in self.consumer:
            try:
                (
                    event_data,
                    order_id,
                    idempotency_key,
                ) = await self._handle_message(msg)
                if not order_id:
                    api_logger.error("errr: невалидное сообщение")
                    await self.consumer.commit()
                    continue

                await self._save_to_inbox(
                    event_data, order_id, idempotency_key
                )
                await self.consumer.commit()
                api_logger.info("saved to inbox and committed")

            except Exception as e:
                api_logger.error("сonsumer Error %s", e, exc_info=True)
                await self.consumer.commit()
                continue
