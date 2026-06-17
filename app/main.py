import asyncio

from fastapi import FastAPI

from app.core.logs_config import api_logger
from app.infrastructure.kafka.consumer import KafkaConsumer
from app.infrastructure.kafka.producer import KafkaProducer
from app.infrastructure.workers.outbox_worker import OutBoxWorker
from app.presentation.midlewares import ErrorHandlingMiddleware
from app.presentation.routers import router


async def lifespan(app: FastAPI):
    api_logger.info("Запуск Outbox worker и consumer")
    producer = KafkaProducer()
    consumer = KafkaConsumer()
    worker = OutBoxWorker(broker=producer)
    api_logger.info("Outbox worker запущен")
    consumer_task = asyncio.create_task(consumer.consume())
    worker_task = asyncio.create_task(worker.work(delay=10))

    yield
    consumer_task.cancel()
    worker_task.cancel()
    await producer.stop()
    api_logger.info("Outbox worker остановлен")


app = FastAPI(lifespan=lifespan)

app.add_middleware(ErrorHandlingMiddleware)
app.include_router(router)
