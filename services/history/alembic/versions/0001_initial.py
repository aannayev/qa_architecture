"""initial history schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-04-11
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("external_id", sa.String(length=64), nullable=False, unique=True),
        sa.Column("topic", sa.String(length=64), nullable=False),
        sa.Column(
            "difficulty",
            sa.Enum("easy", "medium", "hard", name="difficulty"),
            nullable=False,
        ),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("options", postgresql.JSONB(), nullable=False),
        sa.Column("correct_index", sa.Integer(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_questions_topic", "questions", ["topic"])
    op.create_index("ix_questions_topic_difficulty", "questions", ["topic", "difficulty"])


def downgrade() -> None:
    op.drop_index("ix_questions_topic_difficulty", table_name="questions")
    op.drop_index("ix_questions_topic", table_name="questions")
    op.drop_table("questions")
    sa.Enum(name="difficulty").drop(op.get_bind(), checkfirst=True)
