"""Organization repository"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from axion_server.models.entities import Org
from axion_server.repositories.base import generate_id, utc_now
from axion.schemas.org import OrgCreate


class OrgRepository:
    """Repository for Organization operations"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: OrgCreate) -> Org:
        """Create a new organization"""
        org = Org(
            org_id=generate_id(),
            name=data.name,
            created_at=utc_now(),
        )
        self.session.add(org)
        await self.session.flush()
        return org

    async def get_by_id(self, org_id: str) -> Org | None:
        """Get organization by ID"""
        result = await self.session.execute(select(Org).where(Org.org_id == org_id))
        return result.scalar_one_or_none()

    async def list_all(
        self, limit: int = 20, cursor: str | None = None
    ) -> tuple[list[Org], str | None]:
        """List organizations with cursor pagination"""
        query = select(Org).order_by(Org.created_at.desc())

        if cursor:
            # Cursor is the org_id of the last item
            cursor_org = await self.get_by_id(cursor)
            if cursor_org:
                query = query.where(Org.created_at < cursor_org.created_at)

        query = query.limit(limit + 1)
        result = await self.session.execute(query)
        orgs = list(result.scalars().all())

        next_cursor = None
        if len(orgs) > limit:
            orgs = orgs[:limit]
            next_cursor = orgs[-1].org_id

        return orgs, next_cursor
