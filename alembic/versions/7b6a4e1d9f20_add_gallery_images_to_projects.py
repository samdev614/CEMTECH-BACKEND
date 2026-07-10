"""Add gallery_images to projects

Revision ID: 7b6a4e1d9f20
Revises: 4d2a7e6c9b1f
Create Date: 2026-07-10 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7b6a4e1d9f20"
down_revision: Union[str, None] = "4d2a7e6c9b1f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("gallery_images", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("projects", "gallery_images")
