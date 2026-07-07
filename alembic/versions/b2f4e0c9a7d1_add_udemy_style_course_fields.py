"""Add Udemy-style course fields

Revision ID: b2f4e0c9a7d1
Revises: 833731ea38e2
Create Date: 2026-07-07 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b2f4e0c9a7d1"
down_revision: Union[str, None] = "833731ea38e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("courses", sa.Column("subtitle", sa.String(length=300), nullable=True))
    op.add_column("courses", sa.Column("language", sa.String(length=50), nullable=True))
    op.add_column("courses", sa.Column("what_you_will_learn", sa.Text(), nullable=True))
    op.add_column("courses", sa.Column("requirements", sa.Text(), nullable=True))
    op.add_column("courses", sa.Column("includes", sa.Text(), nullable=True))
    op.add_column("courses", sa.Column("course_content", sa.Text(), nullable=True))
    op.add_column("courses", sa.Column("target_audience", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("courses", "target_audience")
    op.drop_column("courses", "course_content")
    op.drop_column("courses", "includes")
    op.drop_column("courses", "requirements")
    op.drop_column("courses", "what_you_will_learn")
    op.drop_column("courses", "language")
    op.drop_column("courses", "subtitle")
