"""add_sort_order_to_documentation

Revision ID: 5ece58e7b2a0
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
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    if 'documentation' not in existing_tables:
        op.create_table(
            'documentation',
            sa.Column('id', sa.Integer(), primary_key=True, index=True),
            sa.Column('title', sa.String(300), nullable=False),
            sa.Column('slug', sa.String(300), nullable=False, unique=True, index=True),
            sa.Column('excerpt', sa.Text(), nullable=True),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('cover_image', sa.String(), nullable=True),
            sa.Column('category', sa.String(100), nullable=True),
            sa.Column('sort_order', sa.Integer(), nullable=True, server_default='0'),
            sa.Column('is_published', sa.Boolean(), nullable=True, server_default='false'),
            sa.Column('author_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        )
    else:
        existing_columns = [c['name'] for c in inspector.get_columns('documentation')]
        if 'sort_order' not in existing_columns:
            op.add_column('documentation', sa.Column('sort_order', sa.Integer(), nullable=True, server_default='0'))


def downgrade() -> None:
    op.drop_table('documentation')
