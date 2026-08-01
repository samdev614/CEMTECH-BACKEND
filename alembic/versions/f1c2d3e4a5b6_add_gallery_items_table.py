"""Add gallery items table

Revision ID: f1c2d3e4a5b6
Revises: 7b6a4e1d9f20
Create Date: 2026-08-01 21:10:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f1c2d3e4a5b6"
down_revision: Union[str, None] = "7b6a4e1d9f20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "gallery_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("alt_text", sa.String(length=255), nullable=True),
        sa.Column("image_url", sa.String(), nullable=False),
        sa.Column("is_published", sa.Boolean(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_gallery_items_id"), "gallery_items", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_gallery_items_id"), table_name="gallery_items")
    op.drop_table("gallery_items")
