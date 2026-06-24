from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.domain_exceptions import (
    IdempotencyError,
    NotEnoughStockError,
    ObjectNotFound,
)
from app.core.http_exceptions import ClientServerError, WrongRequest
from app.core.logs_config import api_logger


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except ObjectNotFound as e:
            api_logger.error("ошибка в эндпоинте %s %s", request.url, e)
            return JSONResponse(status_code=404, content={"detail": str(e)})
        except (ValueError, WrongRequest, NotEnoughStockError) as e:
            api_logger.error("ошибка в эндпоинте %s %s", request.url, str(e))
            return JSONResponse(status_code=400, content={"detail": str(e)})
        except ClientServerError as e:
            api_logger.error("ошибка в эндпоинте %s %s", request.url, str(e))
            return JSONResponse(
                status_code=e.status_code, content={"detail": str(e)}
            )
        except IdempotencyError as e:
            api_logger.error("ошибка в эндпоинте %s %s", request.url, str(e))
            return JSONResponse(status_code=409, content={"detail": str(e)})

        except Exception as e:
            api_logger.error("Ошибка сервера: %s", e, exc_info=True)
            return JSONResponse(
                status_code=500, content={"detail": "Внутренняя ошибка"}
            )
