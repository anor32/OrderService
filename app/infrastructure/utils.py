import asyncio
from urllib.parse import urljoin

from httpx import URL, AsyncClient, Request, Response

from app.core.exceptions import ObjectNotFound
from app.infrastructure.error_handlers import ClientServerError, WrongRequest


def build_url(base_url: str | URL, path: str) -> str:
    if not isinstance(base_url, str):
        base_url = str(base_url)

    base = base_url.rstrip("/")
    path = path.lstrip("/")

    return urljoin(base + "/", path)


async def retry_request(
    client: AsyncClient, request: Request, max_retry=3, delay=1
) -> Response:
    retry = 1
    response = await client.send(request)
    while retry <= max_retry and response.is_server_error:
        retry += 1
        await asyncio.sleep(delay)
        response = await client.send(request)

    if response.is_success:
        return response
    elif response.is_server_error:
        raise ClientServerError(
            "Ошибка внешнего сервера попробуйте позже", status_code=503
        )
    elif response.status_code == 404:
        raise ObjectNotFound(
            "Ошибка запрашиваемые данные от клиента не найдены "
        )
    elif response.is_client_error:
        raise WrongRequest(
            f"Ошибка неправильный запрос клиента {response.text}", 400
        )
