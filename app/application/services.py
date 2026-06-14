from datetime import datetime
from typing import Any

from app.core.config import CALLBACK_URL
from app.core.interfaces import CatalogService, PaymentService, UnitOfWork
from app.core.schemas import (
    CreateOrderRequest,
    CreatePaymentRequest,
    Order,
    OrderStatus,
    OutboxStatus,
    PaymentResponse,
    PaymentStatus,
)


class OrderService:
    def __init__(
        self,
        uow: UnitOfWork,
        catalog: CatalogService,
        payment_service: PaymentService,
    ):
        self.uow = uow
        self.catalog = catalog
        self.payment_service = payment_service

    async def get_order(self, order_id: str) -> Order:
        async with self.uow as u:
            order = await u.order_repo.get_by_id(order_id)
            return order

    async def create_order(self, order_request: CreateOrderRequest) -> Order:
        inbox = await self._check_idempotency(
            key=order_request.idempotency_key,
            payload=order_request.model_dump(mode="json"),
        )
        if inbox:
            return inbox
        store = await self.catalog.check_item(item_id=order_request.item_id)
        store.is_available(order_request.quantity)

        result = await self._transactional_save(order_request)
        payment_data = CreatePaymentRequest(
            order_id=result.id,
            amount=store.price,
            callback_url=CALLBACK_URL,
            idempotency_key=order_request.idempotency_key,
        )
        await self.payment_service.create_payment(payment_data)
        return result

    async def _check_idempotency(
        self,
        key: str,
        payload: dict[str, Any],
    ) -> Order | None:
        inbox = await self.uow.inbox_repo.get_by_idempotency_key(key)
        if inbox:
            await self.uow.inbox_repo.check_idempotency(
                key=inbox.idempotency_key,
                payload=payload,
            )
            return Order(**inbox.result)
        return

    async def _transactional_save(
        self,
        order_request: CreateOrderRequest,
    ) -> Order:
        dto = self.uow.order_repo.CreateDTO(
            user_id=order_request.user_id,
            item_id=order_request.item_id,
            quantity=order_request.quantity,
        )
        outbox_dto = self.uow.outbox_repo.CreateDTO(
            event_type="create_order",
            payload=order_request.model_dump(mode="json"),
            status=OutboxStatus.PENDING,
            created_at=datetime.now(),
        )
        try:
            async with self.uow as u:
                created_order = await u.order_repo.create(dto)
                await u.outbox_repo.create_outbox(outbox_dto)
                inbox_dto = u.inbox_repo.CreateDTO(
                    idempotency_key=order_request.idempotency_key,
                    payload=order_request.model_dump(mode="json"),
                    result=created_order.model_dump(mode="json"),
                )
                await u.inbox_repo.save(inbox_dto)
        except Exception as e:
            raise e
        return created_order

    async def process_payment_callback(self, payment: PaymentResponse):
        inbox = self._check_idempotency(
            key=payment.idempotency_key,
            payload=payment.model_dump(mode="json"),
        )
        if inbox:
            return
        if payment.status == PaymentStatus.SUCCEEDED:
            db_status = OrderStatus.PAID
        else:
            db_status = OrderStatus.CANCELLED

        with self.uow as u:
            await u.order_repo.set_order_status(db_status)
            dto = await u.inbox_repo.CreateDTO(
                idempotency_key=payment.idempotency_key,
                payload=payment.model_dump(),
                result={"success": True},
            )
            u.inbox_repo.save(dto)
