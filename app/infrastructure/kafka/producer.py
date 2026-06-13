from aiokafka import AIOKafkaProducer


class KafkaProducer:
    def __init__(self):
        self._started = False
        self._producer = None

    def _init_producer(self):
        if not self._producer:
            self._producer = AIOKafkaProducer(
                bootstrap_servers="localhost:9092",
                value_serializer=lambda x: x.encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8"),
            )

    async def _start(self):
        await self._producer.start()

    async def send_to_kafka(self, topic, value, key):
        if not self._started:
            raise RuntimeError("Нет подходящего producer")
        await self._producer.send(topic=topic, value=value, key=key)

    async def create_producer(self):
        self._init_producer()
        await self._start()
        self._started = True
        return self


# глобальные задачи на завтра применить инбокс патерн доделать outbox
# полностью сделать метод создание в бизнес логике
