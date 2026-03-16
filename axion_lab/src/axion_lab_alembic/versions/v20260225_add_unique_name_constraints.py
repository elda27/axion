"""Add unique name constraints to orgs, projects, batches

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-02-25

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: str | Sequence[str] | None = "b2c3d4e5f6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Use unique indexes for SQLite compatibility
    op.create_index("uq_orgs_name", "orgs", ["name"], unique=True)

    # Project name must be unique within an organization
    op.create_index("uq_projects_org_name", "projects", ["org_id", "name"], unique=True)

    # Batch name must be unique within a project
    op.create_index("uq_batches_project_name", "batches", ["project_id", "name"], unique=True)


def downgrade() -> None:
    op.drop_index("uq_batches_project_name", table_name="batches")
    op.drop_index("uq_projects_org_name", table_name="projects")
    op.drop_index("uq_orgs_name", table_name="orgs")
