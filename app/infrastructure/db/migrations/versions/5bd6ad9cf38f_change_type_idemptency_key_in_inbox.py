"""change type idemptency key in inbox

Revision ID: 5bd6ad9cf38f
Revises: c9fdec457a42
Create Date: 2026-06-13 22:16:13.482068

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5bd6ad9cf38f'
down_revision: Union[str, Sequence[str], None] = 'c9fdec457a42'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('inbox', 'idempotency_key',
               existing_type=sa.UUID(),
               type_=sa.String(),
               existing_nullable=False,
               postgresql_using="idempotency_key::text")
    op.create_unique_constraint('uq_inbox_idempotency_key', 'inbox', ['idempotency_key'])


def downgrade() -> None:
    op.drop_constraint('uq_inbox_idempotency_key', 'inbox', type_='unique')
    op.alter_column('inbox', 'idempotency_key',
               existing_type=sa.String(),
               type_=sa.UUID(),
               existing_nullable=False,
               postgresql_using="idempotency_key::uuid")
    # ### end Alembic commands ###
