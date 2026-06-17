import asyncio

from fastapi import FastAPI

from app.core.logs_config import api_logger
from app.infrastructure.kafka.consumer import KafkaConsumer
from app.infrastructure.kafka.producer import KafkaProducer
from app.infrastructure.workers.Inbox_worker import InboxWorker
from app.infrastructure.workers.outbox_worker import OutBoxWorker
from app.presentation.middlewares import ErrorHandlingMiddleware
from app.presentation.routers import router


async def lifespan(app: FastAPI):
    api_logger.info("Запуск Outbox worker и consumer")
    producer = KafkaProducer()
    consumer = KafkaConsumer()
    worker = OutBoxWorker(broker=producer)
    inbox_worker = InboxWorker()
    api_logger.info("Outbox worker запущен")
    consumer_task = asyncio.create_task(consumer.consume())
    worker_task = asyncio.create_task(worker.work(delay=10))
    inbox_worker = asyncio.create_task(inbox_worker.work(delay=10, limit=100))
    yield
    inbox_worker.cancel()
    consumer_task.cancel()
    worker_task.cancel()
    await producer.stop()
    await consumer.stop()
    api_logger.info("Outbox worker остановлен")


app = FastAPI(lifespan=lifespan)

app.add_middleware(ErrorHandlingMiddleware)
app.include_router(router)
