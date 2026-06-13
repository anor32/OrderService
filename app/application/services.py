from app.core.interfaces import UnitOfWork
from app.core.schemas import CreateOrderRequest, Order, Outbox


class OrderService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def create_order(self, order: CreateOrderRequest) -> Order:
        inbox = await self.uow.inbox_repo.get_by_idempotency_key(
            order.idempotency_key
        )
        if inbox:
            await self.uow.inbox_repo.check_idempotency(
                key=inbox.idempotency_key,
                payload=order.model_dump(mode="json"),
            )
            return Order(**inbox.result)
        ord = Order(**order.model_dump())
        dto = self.uow.order_repo.CreateDTO(
            user_id=ord.user_id,
            item_id=ord.item_id,
            quantity=ord.quantity,
        )
        out = Outbox(
            event_type="create_order", payload=ord.model_dump(mode="json")
        )
        outbox_dto = self.uow.outbox_repo.CreateDTO(
            event_type=out.event_type,
            payload=out.payload,
            status=out.status,
            created_at=out.created_at,
        )
        try:
            async with self.uow as u:
                result = await u.order_repo.create(dto)
                await u.outbox_repo.create_outbox(outbox_dto)
                inbox_dto = u.inbox_repo.CreateDTO(
                    idempotency_key=order.idempotency_key,
                    payload=order.model_dump(mode="json"),
                    result=result.model_dump(mode="json"),
                )
                await u.inbox_repo.save(inbox_dto)
        except Exception as e:
            raise e

        return result
