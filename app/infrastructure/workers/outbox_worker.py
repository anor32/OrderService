import asyncio
import json

from aiokafka.structs import RecordMetadata

from app.core.logs_config import api_logger
from app.infrastructure.db.db_config import AsyncSession
from app.infrastructure.db.repository import OutboxRepositoryImpl
from app.infrastructure.db.unit_of_work import (
    UnitOfWorkWorker,
)
from app.infrastructure.kafka.producer import KafkaProducer


class OutBoxWorker:
    def __init__(self, broker: KafkaProducer):
        self._broker = broker

    async def _init_unitOfwork(self, session: AsyncSession):
        outbox = OutboxRepositoryImpl(session)
        return UnitOfWorkWorker(
            session=session,
            outbox_repo=outbox,
        )

    async def init_worker(self):
        try:
            await self._broker.create_producer()
        except Exception as e:
            api_logger.error("Ошибка инициализации кафки %s", e)
            return False
        else:
            return True

    async def broker_send(
        self, message: str, idempotency_key: str
    ) -> RecordMetadata | None:
        try:
            result = await self._broker.send_to_kafka(
                topic="student_system-order.events",
                value=str(message),
                key=str(idempotency_key),
            )

        except Exception as e:
            api_logger.error("Ошибка отправки в кафку %s", e)
            return
        else:
            api_logger.info(
                "отправка в кафку статус %s %s",
                result,
                type(result),
            )
        return result

    async def process(self):
        async with AsyncSession() as session:
            unit_of_work = await self._init_unitOfwork(session)
            async with unit_of_work as uow:
                records = await uow.outbox_repo.get_records()
                ids = []
                for record in records:
                    data_to_send = record.payload
                    idempotency_key = data_to_send.get("idempotency_key")

                    event_type = data_to_send.get("event_type")
                    data_to_send["event_type"] = "order." + event_type.lower()
                    message = json.dumps(record.payload)
                    api_logger.info(message)

                    result = await self.broker_send(
                        message, str(idempotency_key)
                    )
                    if not result:
                        continue
                    ids.append(str(record.id))
                if ids:
                    await uow.outbox_repo.set_sent_status(ids)

    async def work(self, delay=20):
        init = await self.init_worker()

        while not init:
            init = await self.init_worker()
            await asyncio.sleep(delay * 60)
        while True:
            await self.process()
            await asyncio.sleep(delay=delay)
