import asyncio

from app.core.interfaces import UnitOfWork
from app.infrastructure.kafka.producer import KafkaProducer


class OutBoxWorker:
    def __init__(self, broker: KafkaProducer, uow: UnitOfWork):
        self._broker = broker
        self._broker.create_producer()
        self.uow = uow

    async def process(self):
        async with self.uow as uow:
            records = await uow.outbox_repo.get_records()
            ids = []

            for record in records:
                order_id = record.order_id
                message = record.payload
                await self._broker.send_to_kafka(
                    topic=record.event_type, value=message, key=order_id
                )
                ids.append(record.id)
            if ids:
                await uow.outbox_repo.set_sent_status(ids)

    async def work(self, delay=10):
        while True:
            await self.process()
            await asyncio.sleep(delay=delay)
