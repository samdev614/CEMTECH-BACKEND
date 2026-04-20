"""add video_url to projects

Revision ID: a1b2c3d4e5f6
Revises: 6ddf97560ef0
Create Date: 2026-04-20 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '6ddf97560ef0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('projects', sa.Column('video_url', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('projects', 'video_url')
