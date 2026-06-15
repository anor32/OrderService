import asyncio
import logging

from fastapi import FastAPI

from app.infrastructure.kafka.producer import KafkaProducer
from app.infrastructure.workers.outbox_worker import OutBoxWorker
from app.presentation.midlewares import ErrorHandlingMiddleware
from app.presentation.routers import router

logger = logging.getLogger(__name__)


async def lifespan(app: FastAPI):
    logger.info("Запуск Outbox worker")
    producer = KafkaProducer()
    worker = OutBoxWorker(broker=producer)
    logger.info("Outbox worker запущен")

    worker_task = asyncio.create_task(worker.work(delay=10))

    yield

    worker_task.cancel()
    await producer.stop()
    logger.info("Outbox worker остановлен")


app = FastAPI(lifespan=lifespan)

app.add_middleware(ErrorHandlingMiddleware)
# app.add_middleware(MetricsMiddleware)
app.include_router(router)
