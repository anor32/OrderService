from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.schemas.statuses import InboxStatus, OrderStatus, OutboxStatus
from app.infrastructure.db.db_config import Base


class OrderModel(Base):
    __tablename__ = "orders"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    item_id: Mapped[UUID] = mapped_column(nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[OrderStatus] = mapped_column(
        String(50), nullable=False, default=OrderStatus.NEW
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now, onupdate=datetime.now
    )


class OutboxModel(Base):
    __tablename__ = "outbox"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[OutboxStatus] = mapped_column(
        String(20), default=OutboxStatus.PENDING, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, nullable=False
    )
    sent_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)


class InboxModel(Base):
    __tablename__ = "inbox"
    idempotency_key: Mapped[str] = mapped_column(
        primary_key=True,
        unique=True,
    )
    status: Mapped[InboxStatus] = mapped_column(
        default=InboxStatus.PENDING, nullable=False
    )
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    result: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, nullable=False
    )
