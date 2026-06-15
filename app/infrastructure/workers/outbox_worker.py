import asyncio
import json

from app.infrastructure.db.db_config import AsyncSession
from app.infrastructure.db.repository import OutboxRepositoryImpl
from app.infrastructure.db.unit_of_work import (
    UnitOfWorkWorker,
)
from app.infrastructure.kafka.producer import KafkaProducer
from app.presentation.logs_config import api_logger


class OutBoxWorker:
    def __init__(self, broker: KafkaProducer):
        self._broker = broker

    async def _init_unitOfwork(self):
        async with AsyncSession() as session:
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

    async def process(self):
        api_logger.info("процессинг начат")
        unit_of_work = await self._init_unitOfwork()
        async with unit_of_work as uow:
            records = await uow.outbox_repo.get_records()
            ids = []
            for record in records:
                idempotency_key = record.payload["idempotency_key"]

                message = json.dumps(record.payload)
                try:
                    await self._broker.send_to_kafka(
                        topic="student_system-order.events",
                        value=message,
                        key=idempotency_key,
                    )
                except Exception as e:
                    api_logger.error("Ошибка отправки в кафку %s", e)
                    return
                else:
                    api_logger.info("отправка в кафку успешна")
                ids.append(str(record.id))
            if ids:
                await uow.outbox_repo.set_sent_status(ids)

    async def work(self, delay=20):
        init = await self.init_worker()
        while not init:
            init = await self.init_worker()
            await asyncio.sleep(delay)
        while True:
            await self.process()
            api_logger.info("процессинг завершен")
            await asyncio.sleep(delay=delay)
