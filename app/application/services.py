from app.core.interfaces import UnitOfWork
from app.core.schemas import CreateOrderRequest


class OrderService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def create_order(self, body: CreateOrderRequest):
        dto = self.uow.order_repo.CreateDTO(
            user_id=body.user_id, item_id=body.item_id, quantity=body.quantity
        )
        outbox_dto = self.uow.outbox_repo.CreateDTO(
            event_type="create_order", payload=dto.model_dump()
        )
        try:
            async with self.uow as u:
                await u.order_repo.create(dto)
                await u.outbox_repo.create_outbox(outbox_dto)

        except Exception as e:
            raise e
