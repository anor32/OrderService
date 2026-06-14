from uuid import UUID

import httpx

from app.core.config import CAPASHINO_HOST, EVENTS_API_KEY
from app.core.interfaces import CatalogService, PaymentService
from app.core.schemas import (
    CatalogResponse,
    CreatePaymentRequest,
)
from app.infrastructure.utils import build_url, retry_request


class CapashinoClient:
    _base_url = CAPASHINO_HOST.rstrip("/")
    _headers = {
        "x-api-key": EVENTS_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


class NotificationService(CapashinoClient):
    async def send_notification(self, body) -> dict:
        url = build_url(self._base_url, "/api/notifications")
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=body, headers=self._headers)

            if response.status_code > 399:
                response = await retry_request(
                    client, response.request, max_retry=3, delay=1
                )
            if response.is_success:
                return response.json()


class CatalogServiceImpl(CapashinoClient, CatalogService):
    async def check_item(self, item_id: UUID) -> CatalogResponse:
        url = build_url(
            base_url=self._base_url, path=f"/api/catalog/items/{item_id}"
        )
        async with httpx.AsyncClient() as client:
            response = await client.get(url=url, headers=self._headers)
            if not response.is_success:
                await retry_request(client, response.request)
        resp = CatalogResponse(**response.json())

        return resp


class PaymentServiceImpl(CapashinoClient, PaymentService):
    async def create_payment(self, body: CreatePaymentRequest):
        url = build_url(base_url=self._base_url, path="/api/payments/")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, data=body.model_dump(mode="json"), headers=self._headers
            )
            if response.is_success:
                await retry_request(client, response.request)
