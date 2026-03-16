"""Rename quality_metrics table to run_metrics

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-02-23

"""

from collections.abc import Sequence

from alembic import context, op

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    dialect_name = context.get_context().dialect.name

    # Rename the table
    op.rename_table("quality_metrics", "run_metrics")

    # Rename index
    op.drop_index("ix_quality_metrics_run_computed", table_name="run_metrics")
    op.create_index(
        "ix_run_metrics_run_computed",
        "run_metrics",
        ["run_id", "computed_at"],
    )

    # Rename unique constraint (SQLite does not support ALTER CONSTRAINT)
    if dialect_name != "sqlite":
        op.drop_constraint("uq_qm_run_key_version", "run_metrics", type_="unique")
        op.create_unique_constraint(
            "uq_rm_run_key_version",
            "run_metrics",
            ["run_id", "key", "version"],
        )


def downgrade() -> None:
    dialect_name = context.get_context().dialect.name

    # Revert unique constraint
    if dialect_name != "sqlite":
        op.drop_constraint("uq_rm_run_key_version", "run_metrics", type_="unique")
        op.create_unique_constraint(
            "uq_qm_run_key_version",
            "run_metrics",
            ["run_id", "key", "version"],
        )

    # Revert index
    op.drop_index("ix_run_metrics_run_computed", table_name="run_metrics")
    op.create_index(
        "ix_quality_metrics_run_computed",
        "run_metrics",
        ["run_id", "computed_at"],
    )

    # Revert table rename
    op.rename_table("run_metrics", "quality_metrics")
