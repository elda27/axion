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
    # Org name must be globally unique
    op.create_unique_constraint("uq_orgs_name", "orgs", ["name"])

    # Project name must be unique within an organization
    op.create_unique_constraint("uq_projects_org_name", "projects", ["org_id", "name"])

    # Batch name must be unique within a project
    op.create_unique_constraint(
        "uq_batches_project_name", "batches", ["project_id", "name"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_batches_project_name", "batches", type_="unique")
    op.drop_constraint("uq_projects_org_name", "projects", type_="unique")
    op.drop_constraint("uq_orgs_name", "orgs", type_="unique")
