"""add_created_at_to_inbox

Revision ID: 3821b5b9ef2c
Revises: c51ea43cceb5
Create Date: 2026-06-14 01:31:12.732856

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3821b5b9ef2c'
down_revision: Union[str, Sequence[str], None] = 'c51ea43cceb5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.execute("""
        ALTER TABLE inbox ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW();
    """)


def downgrade() -> None:
    """Downgrade schema."""

    op.execute("ALTER TABLE inbox DROP COLUMN IF EXISTS created_at")
