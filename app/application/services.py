from app.core.interfaces import UnitOfWork
from app.core.schemas import CreateOrderRequest, Order


class OrderService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def create_order(self, order: CreateOrderRequest) -> Order:
        inbox = await self.uow.inbox_repo.get_by_idempotency_key(
            order.idempotency_key
        )
        if inbox:
            await self.uow.inbox_repo.check_idempotency(
                key=inbox.idempotency_key, payload=order.model_dump()
            )
        dto = self.uow.order_repo.CreateDTO(
            user_id=order.user_id,
            item_id=order.item_id,
            quantity=order.quantity,
        )
        outbox_dto = self.uow.outbox_repo.CreateDTO(
            event_type="create_order", payload=dto.model_dump()
        )
        try:
            async with self.uow as u:
                result = await u.order_repo.create(dto)
                await u.outbox_repo.create_outbox(outbox_dto)
                inbox_dto = u.inbox_repo.CreateDTO(
                    idempotency_key=order.idempotency_key,
                    payload=order.model_dump(),
                    result=result.model_dump(),
                )
                await u.inbox_repo.save(inbox_dto)
        except Exception as e:
            raise e

        return result
