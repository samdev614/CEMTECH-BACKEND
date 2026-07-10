"""Add course sections and lessons

Revision ID: 9c971684b140
Revises: b2f4e0c9a7d1
Create Date: 2026-07-08 00:05:21.366170

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = '9c971684b140'
down_revision: Union[str, None] = 'b2f4e0c9a7d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _inspector():
    return inspect(op.get_bind())


def _table_exists(inspector, table_name: str) -> bool:
    return inspector.has_table(table_name)


def _column_names(inspector, table_name: str) -> set[str]:
    return {column["name"] for column in inspector.get_columns(table_name)}


def _index_names(inspector, table_name: str) -> set[str]:
    return {index["name"] for index in inspector.get_indexes(table_name)}


def _drop_unique_constraint_by_columns(inspector, table_name: str, column_names: list[str]) -> bool:
    for constraint in inspector.get_unique_constraints(table_name):
        if constraint.get("column_names") == column_names:
            op.drop_constraint(constraint["name"], table_name, type_="unique")
            return True
    return False


def _create_course_sections_table() -> None:
    op.create_table(
        "course_sections",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("course_id", sa.Integer(), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_course_sections_id"), "course_sections", ["id"], unique=False)


def _create_course_lessons_table() -> None:
    op.create_table(
        "course_lessons",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("section_id", sa.Integer(), sa.ForeignKey("course_sections.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("video_url", sa.String(), nullable=True),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_course_lessons_id"), "course_lessons", ["id"], unique=False)


def _normalize_course_sections(inspector) -> None:
    table_name = "course_sections"
    columns = _column_names(inspector, table_name)
    indexes = _index_names(inspector, table_name)

    if "order" not in columns:
        op.add_column(
            table_name,
            sa.Column("order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        )
        if "sort_order" in columns:
            op.execute(sa.text('UPDATE course_sections SET "order" = COALESCE(sort_order, 0)'))
        op.alter_column(table_name, "order", server_default=None)

    if "title" in columns:
        op.alter_column(
            table_name,
            "title",
            existing_type=sa.VARCHAR(length=300),
            type_=sa.String(length=255),
            existing_nullable=False,
        )

    if "ix_course_sections_course_id" in indexes:
        op.drop_index("ix_course_sections_course_id", table_name=table_name)
    if "ix_course_sections_id" not in indexes:
        op.create_index(op.f("ix_course_sections_id"), table_name, ["id"], unique=False)

    if "sort_order" in columns:
        op.drop_column(table_name, "sort_order")


def _normalize_course_lessons(inspector) -> None:
    table_name = "course_lessons"
    columns = _column_names(inspector, table_name)
    indexes = _index_names(inspector, table_name)

    if "order" not in columns:
        op.add_column(
            table_name,
            sa.Column("order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        )
        if "sort_order" in columns:
            op.execute(sa.text('UPDATE course_lessons SET "order" = COALESCE(sort_order, 0)'))
        op.alter_column(table_name, "order", server_default=None)

    if "title" in columns:
        op.alter_column(
            table_name,
            "title",
            existing_type=sa.VARCHAR(length=300),
            type_=sa.String(length=255),
            existing_nullable=False,
        )

    if "video_url" in columns:
        op.alter_column(table_name, "video_url", existing_type=sa.VARCHAR(), nullable=True)

    if "ix_course_lessons_section_id" in indexes:
        op.drop_index("ix_course_lessons_section_id", table_name=table_name)
    if "ix_course_lessons_id" not in indexes:
        op.create_index(op.f("ix_course_lessons_id"), table_name, ["id"], unique=False)

    if "sort_order" in columns:
        op.drop_column(table_name, "sort_order")


def _normalize_orders(inspector) -> None:
    table_name = "orders"

    _drop_unique_constraint_by_columns(inspector, table_name, ["idempotency_key"])
    _drop_unique_constraint_by_columns(inspector, table_name, ["invoice_number"])

    refreshed = _inspector()
    unique_indexes = {
        tuple(index["column_names"])
        for index in refreshed.get_indexes(table_name)
        if index.get("unique")
    }

    if ("idempotency_key",) not in unique_indexes:
        op.create_index(op.f("ix_orders_idempotency_key"), table_name, ["idempotency_key"], unique=True)
    if ("invoice_number",) not in unique_indexes:
        op.create_index(op.f("ix_orders_invoice_number"), table_name, ["invoice_number"], unique=True)


def upgrade() -> None:
    inspector = _inspector()

    if not _table_exists(inspector, "course_sections"):
        _create_course_sections_table()
    else:
        _normalize_course_sections(inspector)

    if not _table_exists(inspector, "course_lessons"):
        _create_course_lessons_table()
    else:
        _normalize_course_lessons(inspector)

    if _table_exists(inspector, "orders"):
        _normalize_orders(inspector)


def downgrade() -> None:
    inspector = _inspector()

    if _table_exists(inspector, "orders"):
        if "ix_orders_invoice_number" in _index_names(inspector, "orders"):
            op.drop_index(op.f("ix_orders_invoice_number"), table_name="orders")
        if "ix_orders_idempotency_key" in _index_names(inspector, "orders"):
            op.drop_index(op.f("ix_orders_idempotency_key"), table_name="orders")
        if "uq_orders_invoice_number" not in {uc["name"] for uc in inspector.get_unique_constraints("orders")}:
            op.create_unique_constraint("uq_orders_invoice_number", "orders", ["invoice_number"])
        if "uq_orders_idempotency_key" not in {uc["name"] for uc in inspector.get_unique_constraints("orders")}:
            op.create_unique_constraint("uq_orders_idempotency_key", "orders", ["idempotency_key"])

    if _table_exists(inspector, "course_sections"):
        columns = _column_names(inspector, "course_sections")
        indexes = _index_names(inspector, "course_sections")
        if "order" in columns:
            op.drop_column("course_sections", "order")
        if "ix_course_sections_id" in indexes:
            op.drop_index(op.f("ix_course_sections_id"), table_name="course_sections")
        if "ix_course_sections_course_id" not in indexes:
            op.create_index("ix_course_sections_course_id", "course_sections", ["course_id"], unique=False)
        if "sort_order" not in columns:
            op.add_column("course_sections", sa.Column("sort_order", sa.INTEGER(), autoincrement=False, nullable=True))
        op.alter_column(
            "course_sections",
            "title",
            existing_type=sa.String(length=255),
            type_=sa.VARCHAR(length=300),
            existing_nullable=False,
        )

    if _table_exists(inspector, "course_lessons"):
        columns = _column_names(inspector, "course_lessons")
        indexes = _index_names(inspector, "course_lessons")
        if "order" in columns:
            op.drop_column("course_lessons", "order")
        if "ix_course_lessons_id" in indexes:
            op.drop_index(op.f("ix_course_lessons_id"), table_name="course_lessons")
        if "ix_course_lessons_section_id" not in indexes:
            op.create_index("ix_course_lessons_section_id", "course_lessons", ["section_id"], unique=False)
        if "is_preview" not in columns:
            op.add_column("course_lessons", sa.Column("is_preview", sa.BOOLEAN(), autoincrement=False, nullable=True))
        if "duration" not in columns:
            op.add_column("course_lessons", sa.Column("duration", sa.VARCHAR(length=100), autoincrement=False, nullable=True))
        if "sort_order" not in columns:
            op.add_column("course_lessons", sa.Column("sort_order", sa.INTEGER(), autoincrement=False, nullable=True))
        op.alter_column(
            "course_lessons",
            "video_url",
            existing_type=sa.VARCHAR(),
            nullable=False,
        )
        op.alter_column(
            "course_lessons",
            "title",
            existing_type=sa.String(length=255),
            type_=sa.VARCHAR(length=300),
            existing_nullable=False,
        )
