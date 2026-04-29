"""add_sort_order_to_documentation

Revision ID: 5ece58e7b2a0
Revises: b2c3d4e5f6a7
Create Date: 2026-04-29 18:06:23.322551

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '5ece58e7b2a0'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('documentation', sa.Column('sort_order', sa.Integer(), nullable=True, server_default='0'))


def downgrade() -> None:
    op.drop_column('documentation', 'sort_order')
