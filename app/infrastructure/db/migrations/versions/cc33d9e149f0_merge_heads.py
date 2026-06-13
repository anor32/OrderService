"""merge_heads

Revision ID: cc33d9e149f0
Revises: 5bd6ad9cf38f, 9599e996da53
Create Date: 2026-06-13 23:19:01.218152

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cc33d9e149f0'
down_revision: Union[str, Sequence[str], None] = ('5bd6ad9cf38f', '9599e996da53')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
