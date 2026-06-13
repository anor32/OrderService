"""init db

Revision ID: fcf9f75c262e
Revises: 5bd6ad9cf38f
Create Date: 2026-06-14 00:30:26.325864

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON, ENUM


revision: str = 'fcf9f75c262e'
down_revision: Union[str, Sequence[str], None] = '5bd6ad9cf38f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'inboxstatus') THEN
                CREATE TYPE inboxstatus AS ENUM ('PENDING', 'PROCESSED');
            END IF;
        END $$;
    """)


    op.create_table(
        'inbox',
        sa.Column('idempotency_key', sa.String(255), nullable=False),
        sa.Column('status', ENUM('PENDING', 'PROCESSED', name='inboxstatus', create_type=False), nullable=False),
        sa.Column('payload', JSON(), nullable=False),
        sa.Column('result', JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('idempotency_key')
    )

    op.create_table(
        'orders',
        sa.Column('id', UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('item_id', UUID(as_uuid=True), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'outbox',
        sa.Column('id', UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('payload', JSON(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('outbox')
    op.drop_table('orders')
    op.drop_table('inbox')


    op.execute("DROP TYPE IF EXISTS inboxstatus CASCADE")
