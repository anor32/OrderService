from datetime import datetime
from uuid import UUID

from db_config import Session
from sqlalchemy import select, update

from app.core.exceptions import ObjectNotFound
from app.core.interfaces import OrderRepository, OutboxRepository
from app.core.schemas import Order, Outbox
from app.infrastructure.db.models import OrderModel, OutboxModel, OutboxStatus


class OrderRepositoryImpl(OrderRepository):
    def __init__(self, session: Session):
        self._session = session

    async def create(self, data: OrderRepository.CreateDTO):
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


class OutboxRepositoryImpl(OutboxRepository):
    def __init__(self, session: Session):
        self._session = session

    async def create_outbox(self, outbox: OutboxRepository.CreateDTO):
        out = OutboxModel(**outbox.model_dump())
        await self._session.add(out)

    async def get_records(self) -> list[Outbox]:
        records = await (
            self._session.scalars(OutboxModel)
            .where(OutboxModel.status == OutboxStatus.PENDING)
            .all()
        )
        records = [self._construct(record) for record in records]

        return records

    def set_sent_status(self, ids: list[UUID]):
        stmt = (
            update(OutboxModel)
            .where(OutboxModel.id.in_(ids))
            .values(status=OutboxStatus.SENT, sent_at=datetime.now())
        )
        self._session.execute(stmt)

    def _construct(self, model: OutboxModel) -> Outbox:
        outbox = Outbox(
            status=model.status,
            event_type=model.event_type,
            payload=model.payload,
            created_at=model.created_at,
            sent_at=model.sent_at,
        )

        return outbox
