"""Add mpesa_last_query_at to orders

Revision ID: 4d2a7e6c9b1f
Revises: 8f5dbbfa4502
Create Date: 2026-07-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "4d2a7e6c9b1f"
down_revision: Union[str, None] = "8f5dbbfa4502"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("mpesa_last_query_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("orders", "mpesa_last_query_at")
