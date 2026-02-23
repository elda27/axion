"""add aggregation tables

Revision ID: a1b2c3d4e5f6
Revises: 0d7469ec9bff
Create Date: 2026-02-20 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "0d7469ec9bff"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add aggregations and aggregation_members tables."""
    op.create_table(
        "aggregations",
        sa.Column("aggregation_id", sa.String(length=26), nullable=False),
        sa.Column("project_id", sa.String(length=26), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("group_by_keys_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("filter_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.project_id"]),
        sa.PrimaryKeyConstraint("aggregation_id"),
    )
    op.create_index(
        "ix_aggregations_project_created",
        "aggregations",
        ["project_id", "created_at"],
        unique=False,
    )

    op.create_table(
        "aggregation_members",
        sa.Column("member_id", sa.String(length=26), nullable=False),
        sa.Column("aggregation_id", sa.String(length=26), nullable=False),
        sa.Column("run_id", sa.String(length=26), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["aggregation_id"], ["aggregations.aggregation_id"]),
        sa.ForeignKeyConstraint(["run_id"], ["runs.run_id"]),
        sa.PrimaryKeyConstraint("member_id"),
    )
    op.create_index(
        "ix_agg_members_agg_added",
        "aggregation_members",
        ["aggregation_id", "added_at"],
        unique=False,
    )
    op.create_index(
        "ix_agg_members_run",
        "aggregation_members",
        ["run_id"],
        unique=False,
    )
    op.create_unique_constraint(
        "uq_aggregation_run",
        "aggregation_members",
        ["aggregation_id", "run_id"],
    )


def downgrade() -> None:
    """Remove aggregation tables."""
    op.drop_table("aggregation_members")
    op.drop_table("aggregations")
