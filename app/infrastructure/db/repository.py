from uuid import UUID

from db_config import Session
from pydantic import BaseModel
from sqlalchemy import select

from app.core.exceptions import ObjectNotFound
from app.core.interfaces import OrderRepository
from app.core.schemas import Order
from app.infrastructure.db.models import OrderModel


class OrderRepositoryImpl(OrderRepository):
    class CreateDTO(BaseModel):
        user_id: str
        item_id: UUID
        quantity: int

    def __init__(self, session: Session):
        self._session = session

    async def create(self, data: CreateDTO):
        order = OrderModel(**data.model_dump())
        await self._session.add(order)

    async def get_by_id(self, order_id: str) -> Order | None:
        stmt = select(OrderModel).where(OrderModel.id == order_id).limit(1)
        model = self._session.scalars(stmt).first()
        if not model:
            raise ObjectNotFound("Объект Order не найден в базе данных")
        order = await self._construct(model)

        return order

    async def _construct(self, model: OrderModel) -> Order:
        order = Order(
            id=model.id,
            user_id=model.user_id,
            amount=float(model.amount),
            status=model.status,
        )
        return order
