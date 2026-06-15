from typing import Any

from app.core.config import CALLBACK_URL
from app.core.interfaces import (
    CatalogService,
    PaymentService,
    UnitOfWorkOrders,
)
from app.core.schemas.entities import (
    CreateOrderRequest,
    CreatePaymentRequest,
    Order,
    PaymentResponse,
)
from app.core.schemas.statuses import OrderStatus
from app.presentation.logs_config import api_logger


class OrderService:
    def __init__(
        self,
        uow: UnitOfWorkOrders,
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
        api_logger.info("cоздание заказа началось")
        inbox = await self._check_idempotency(
            key=order_request.idempotency_key,
            payload=order_request.model_dump(mode="json"),
        )
        if inbox:
            return inbox
        api_logger.info("проверка на складе")
        store = await self.catalog.check_item(item_id=order_request.item_id)
        store.is_available(order_request.quantity)
        api_logger.info("cохрание заказа  в базу")
        result = await self._transactional_save(order_request)
        payment_data = CreatePaymentRequest(
            order_id=result.id,
            amount=store.price,
            callback_url=CALLBACK_URL,
            idempotency_key=order_request.idempotency_key,
        )
        api_logger.info("Отправка в payment service")
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
        dto = order_request.to_order_dto()

        try:
            async with self.uow as u:
                created_order = await u.order_repo.create(dto)
                inbox_dto = order_request.to_inbox_dto(created_order)
                await u.inbox_repo.save(inbox_dto)
        except Exception as e:
            raise e
        return created_order

    async def process_payment_callback(self, payment: PaymentResponse):
        inbox = self._check_idempotency(
            key=str(payment.payment_id),
            payload=payment.model_dump(mode="json"),
        )
        if inbox:
            return
        db_status = payment.check_status()

        with self.uow as u:
            order = await u.order_repo.get_by_id(payment.order_id)
            await u.order_repo.set_order_status(db_status, payment.id)
            dto = await u.inbox_repo.CreateDTO(
                idempotency_key=payment.idempotency_key,
                payload=payment.model_dump(),
                result={"success": True},
            )

            ev = order.to_order_event(payment=payment)
            outbox_dto = ev.to_outbox_dto()
            await u.outbox_repo.create_outbox(outbox_dto)
            u.inbox_repo.save(dto)

    async def process_shipping_callback(self, status: OrderStatus, order_id):
        async with self.uow as uow:
            await uow.order_repo.set_order_status(status, order_id)
