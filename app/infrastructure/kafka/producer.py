from aiokafka import AIOKafkaProducer
from aiokafka.structs import RecordMetadata

from app.core.config import KAFKA_BOOTSTRAP_SERVERS


class KafkaProducer:
    def __init__(self):
        self._started = False
        self._producer = None

    def _init_producer(self):
        if not self._producer:
            self._producer = AIOKafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda x: x.encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8"),
                enable_idempotence=True,
                acks="all",
            )

    async def _start(self):
        await self._producer.start()

    async def stop(self):
        await self._producer.stop()

    async def send_to_kafka(self, topic, value, key) -> RecordMetadata:
        if not self._started:
            raise RuntimeError("Нет подходящего producer")
        result = await self._producer.send_and_wait(
            topic=topic, value=value, key=key
        )
        return result

    async def create_producer(self):
        self._init_producer()
        await self._start()
        self._started = True
        return self
