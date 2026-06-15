from uuid import UUID

from app.core.interfaces import UnitOfWorkConsumer
from app.core.schemas.statuses import OrderStatus


class OrderProcessor:
    def __init__(self, uow: UnitOfWorkConsumer):
        self.uow = uow

    async def process_shipping_callback(
        self, status: OrderStatus, order_id: UUID
    ):
        async with self.uow as uow:
            await uow.order_repo.set_order_status(status, str(order_id))
            await uow.commit()
