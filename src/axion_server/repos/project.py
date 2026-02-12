"""Project repository"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from axion_server.repos.models.entities import Project
from axion_server.shared.domain import ProjectCreate
from axion_server.shared.libs import generate_id, utc_now


class ProjectRepository:
    """Repository for Project operations"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, org_id: str, data: ProjectCreate) -> Project:
        """Create a new project"""
        project = Project(
            project_id=generate_id(),
            org_id=org_id,
            name=data.name,
            created_at=utc_now(),
        )
        self.session.add(project)
        await self.session.flush()
        return project

    async def get_by_id(self, project_id: str) -> Project | None:
        """Get project by ID"""
        result = await self.session.execute(
            select(Project).where(Project.project_id == project_id)
        )
        return result.scalar_one_or_none()

    async def list_by_org(
        self, org_id: str, limit: int = 20, cursor: str | None = None
    ) -> tuple[list[Project], str | None]:
        """List projects by organization with cursor pagination"""
        query = (
            select(Project)
            .where(Project.org_id == org_id)
            .order_by(Project.created_at.desc())
        )

        if cursor:
            cursor_project = await self.get_by_id(cursor)
            if cursor_project:
                query = query.where(Project.created_at < cursor_project.created_at)

        query = query.limit(limit + 1)
        result = await self.session.execute(query)
        projects = list(result.scalars().all())

        next_cursor = None
        if len(projects) > limit:
            projects = projects[:limit]
            next_cursor = projects[-1].project_id

        return projects, next_cursor
