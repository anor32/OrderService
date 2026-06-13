"""init_db

Revision ID: c51ea43cceb5
Revises: 5bd6ad9cf38f
Create Date: 2026-06-14 01:06:48.796015

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

# revision identifiers, used by Alembic.
revision: str = 'c51ea43cceb5'
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

    op.execute("""
        CREATE TABLE IF NOT EXISTS inbox (
            idempotency_key VARCHAR(255) NOT NULL,
            status inboxstatus NOT NULL,
            payload JSON NOT NULL,
            result JSON NOT NULL,
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
            PRIMARY KEY (idempotency_key)
        );
    """)


    op.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id UUID NOT NULL,
            user_id VARCHAR(255) NOT NULL,
            item_id UUID NOT NULL,
            quantity INTEGER NOT NULL,
            status VARCHAR(50) NOT NULL,
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
            updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
            PRIMARY KEY (id)
        );
    """)


    op.execute("""
        CREATE TABLE IF NOT EXISTS outbox (
            id UUID NOT NULL,
            event_type VARCHAR(100) NOT NULL,
            payload JSON NOT NULL,
            status VARCHAR(20) NOT NULL,
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
            sent_at TIMESTAMP WITHOUT TIME ZONE,
            PRIMARY KEY (id)
        );
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TABLE IF EXISTS outbox CASCADE")
    op.execute("DROP TABLE IF EXISTS orders CASCADE")
    op.execute("DROP TABLE IF EXISTS inbox CASCADE")
    op.execute("DROP TYPE IF EXISTS inboxstatus CASCADE")
