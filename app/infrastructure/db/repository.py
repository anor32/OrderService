from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select, update

from app.core.exceptions import IdempotencyError, ObjectNotFound
from app.core.interfaces import (
    InboxRepository,
    OrderRepository,
    OutboxRepository,
)
from app.core.schemas import InboxEvent, InboxStatus, Order, Outbox
from app.infrastructure.db.db_config import AsyncSession
from app.infrastructure.db.models import (
    InboxModel,
    OrderModel,
    OutboxModel,
    OutboxStatus,
)


class OrderRepositoryImpl(OrderRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, data: OrderRepository.CreateDTO) -> Order:
        order = OrderModel(**data.model_dump())
        self._session.add(order)
        await self._session.flush()
        return await self._construct(order)

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
            item_id=model.item_id,
            quantity=model.quantity,
            status=model.status,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

        return order


class OutboxRepositoryImpl(OutboxRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create_outbox(
        self, outbox: OutboxRepository.CreateDTO
    ) -> Outbox:
        out = OutboxModel(**outbox.model_dump())
        self._session.add(out)
        await self._session.flush()
        return await self._construct(out)

    async def get_records(self) -> list[Outbox]:
        records = await (
            self._session.scalars(OutboxModel)
            .where(OutboxModel.status == OutboxStatus.PENDING)
            .limit(100)
            .with_for_update(skip_locked=True)
            .all()
        )
        records = [await self._construct(record) for record in records]

        return records

    async def set_sent_status(self, ids: list[UUID]):
        stmt = (
            update(OutboxModel)
            .where(OutboxModel.id.in_(ids))
            .values(status=OutboxStatus.SENT, sent_at=datetime.now())
        )
        await self._session.execute(stmt)

    async def _construct(self, model: OutboxModel) -> Outbox:
        outbox = Outbox(
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

    async def get_by_idempotency_key(self, key: UUID) -> InboxEvent | None:
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

    async def save(self, dto: InboxRepository.CreateDTO) -> None:
        existing = await self.get_by_idempotency_key(dto.idempotency_key)

        if existing:
            if existing.payload != dto.payload:
                raise IdempotencyError(
                    f"Payload mismatch for idempotency_key "
                    f"{dto.idempotency_key}"
                )
            return

        model = InboxModel(
            idempotency_key=dto.idempotency_key,
            payload=dto.payload,
            result=dto.result,
            status=InboxStatus.PENDING,
        )
        self._session.add(model)
        await self._session.flush()

    async def check_idempotency(
        self, key: UUID, payload: dict[str, Any]
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
