from datetime import datetime

from app.core.interfaces import UnitOfWork
from app.core.schemas import CreateOrderRequest, Order, OutboxStatus


class OrderService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def create_order(self, order_request: CreateOrderRequest) -> Order:
        inbox = await self._check_idempotency(order_request)
        if inbox:
            return inbox

        result = await self._transactional_save(order_request)
        return result

    async def _check_idempotency(
        self, order: CreateOrderRequest
    ) -> Order | None:
        inbox = await self.uow.inbox_repo.get_by_idempotency_key(
            order.idempotency_key
        )
        if inbox:
            await self.uow.inbox_repo.check_idempotency(
                key=inbox.idempotency_key,
                payload=order.model_dump(mode="json"),
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
