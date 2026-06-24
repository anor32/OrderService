from datetime import datetime
from typing import Any

from sqlalchemy import Select, select, update

from app.core.domain_exceptions import IdempotencyError, ObjectNotFound
from app.core.interfaces import (
    InboxRepository,
    OrderRepository,
    OutboxRepository,
)
from app.core.schemas.dto import InboxDTO, OrderCreateDTO, OutboxDTO
from app.core.schemas.entities import (
    InboxEvent,
    Order,
    Outbox,
)
from app.core.schemas.statuses import InboxStatus, OrderStatus, OutboxStatus
from app.infrastructure.db.db_config import AsyncSession
from app.infrastructure.db.models import (
    InboxModel,
    OrderModel,
    OutboxModel,
)


class OrderRepositoryImpl(OrderRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, data: OrderCreateDTO) -> Order:
        order = OrderModel(**data.model_dump())
        self._session.add(order)
        await self._session.flush()
        return await self._construct(order)

    async def _get_query_by_id(self, order_id) -> Select:
        stmt = select(OrderModel).where(OrderModel.id == order_id).limit(1)
        return stmt

    async def get_by_id(self, order_id: str) -> Order | None:
        stmt = await self._get_query_by_id(order_id)
        model = await self._session.scalar(stmt)
        if not model:
            raise ObjectNotFound("Объект Order не найден в базе данных")
        order = await self._construct(model)

        return order

    async def _construct(self, model: OrderModel) -> Order:
        order = Order(
            id=model.id,
            user_id=model.user_id,
            item_id=model.item_id,
            quantity=model.quantity,
            status=model.status,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

        return order

    async def set_order_status(self, status: OrderStatus, order_id: str):
        stmt = await self._get_query_by_id(order_id)
        model = await self._session.scalar(stmt)
        if not model:
            raise ObjectNotFound("Объект Order не найден в базе данных")
        model.status = status


class OutboxRepositoryImpl(OutboxRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create_outbox(self, outbox: OutboxDTO) -> Outbox:
        out = OutboxModel(**outbox.model_dump())
        self._session.add(out)
        await self._session.flush()
        return await self._construct(out)

    async def get_records(self) -> list[Outbox]:
        stmt = (
            select(OutboxModel)
            .where(OutboxModel.status == OutboxStatus.PENDING)
            .limit(100)
            .with_for_update(skip_locked=True)
        )

        records = await self._session.scalars(stmt)

        records = [await self._construct(record) for record in records.all()]

        return records

    async def set_sent_status(self, ids: list[str]):
        stmt = (
            update(OutboxModel)
            .where(OutboxModel.id.in_(ids))
            .values(status=OutboxStatus.SENT, sent_at=datetime.now())
        )
        await self._session.execute(stmt)

    async def _construct(self, model: OutboxModel) -> Outbox:
        outbox = Outbox(
            id=model.id,
            status=model.status,
            event_type=model.event_type,
            payload=model.payload,
            created_at=model.created_at,
            sent_at=model.sent_at,
        )

        return outbox


class InboxRepositoryImpl(InboxRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_idempotency_key(self, key: str) -> InboxEvent | None:
        stmt = select(InboxModel).where(InboxModel.idempotency_key == key)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_entity(model)

    async def get_pending(self, limit: int = 100) -> list[InboxEvent]:
        stmt = (
            select(InboxModel)
            .where(InboxModel.status == InboxStatus.PENDING)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]

    async def save(self, dto: InboxDTO) -> None:
        await self.check_idempotency(
            key=dto.idempotency_key, payload=dto.payload
        )

        model = InboxModel(
            idempotency_key=dto.idempotency_key,
            payload=dto.payload,
            result=dto.result,
            status=InboxStatus.PENDING,
        )
        self._session.add(model)
        await self._session.flush()

    async def set_status_processed(self, ids: list[str]) -> None:
        stmt = (
            update(InboxModel)
            .where(InboxModel.idempotency_key.in_(ids))
            .values(status=InboxStatus.PROCESSED)
        )
        await self._session.execute(stmt)

    async def check_idempotency(
        self, key: str, payload: dict[str, Any]
    ) -> None:
        existing = await self.get_by_idempotency_key(key)
        if existing and existing.payload != payload:
            raise IdempotencyError(
                f"Idempotency violation: payload mismatch for key {key}"
            )

    def _to_entity(self, model: InboxModel) -> InboxEvent:
        return InboxEvent(
            idempotency_key=model.idempotency_key,
            status=model.status,
            payload=model.payload,
            result=model.result,
            created_at=model.created_at,
        )
