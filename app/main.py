import logging

from fastapi import FastAPI

from app.presentation.midlewares import ErrorHandlingMiddleware
from app.presentation.routers import router

logger = logging.getLogger(__name__)


app = FastAPI()
app.add_middleware(ErrorHandlingMiddleware)
# app.add_middleware(MetricsMiddleware)
app.include_router(router)
