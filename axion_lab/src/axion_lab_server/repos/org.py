"""Organization repository"""

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from axion_lab_server.repos.models.entities import Org
from axion_lab_server.shared.domain import OrgCreate
from axion_lab_server.shared.libs import generate_id, utc_now


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

    async def get_by_name(self, name: str) -> Org | None:
        """Get organization by name"""
        result = await self.session.execute(select(Org).where(Org.name == name))
        return result.scalar_one_or_none()

    async def list_all(
        self, limit: int = 20, cursor: str | None = None
    ) -> tuple[list[Org], str | None]:
        """List organizations with cursor pagination"""
        query = select(Org).order_by(Org.created_at.desc(), Org.org_id.desc())

        if cursor:
            # Cursor is the org_id of the last item
            cursor_org = await self.get_by_id(cursor)
            if cursor_org:
                query = query.where(
                    or_(
                        Org.created_at < cursor_org.created_at,
                        and_(
                            Org.created_at == cursor_org.created_at,
                            Org.org_id < cursor_org.org_id,
                        ),
                    )
                )

        query = query.limit(limit + 1)
        result = await self.session.execute(query)
        orgs = list(result.scalars().all())

        next_cursor = None
        if len(orgs) > limit:
            orgs = orgs[:limit]
            next_cursor = orgs[-1].org_id

        return orgs, next_cursor
