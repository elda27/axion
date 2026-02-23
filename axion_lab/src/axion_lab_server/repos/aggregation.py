"""Aggregation repository"""

import json

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from axion_lab_server.repos.models.entities import Aggregation, AggregationMember
from axion_lab_server.shared.domain import AggregationCreate, AggregationMemberAdd
from axion_lab_server.shared.libs import generate_id, utc_now


class AggregationRepository:
    """Repository for Aggregation and AggregationMember operations"""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ── Aggregation CRUD ──────────────────────────────────────

    async def create(self, project_id: str, data: AggregationCreate) -> Aggregation:
        """Create a new aggregation"""
        aggregation = Aggregation(
            aggregation_id=generate_id(),
            project_id=project_id,
            name=data.name,
            description=data.description,
            group_by_keys_json=json.dumps(data.group_by_keys),
            filter_json=json.dumps(data.filter),
            created_at=utc_now(),
        )
        self.session.add(aggregation)
        await self.session.flush()
        return aggregation

    async def get_by_id(self, aggregation_id: str) -> Aggregation | None:
        """Get aggregation by ID"""
        result = await self.session.execute(
            select(Aggregation).where(Aggregation.aggregation_id == aggregation_id)
        )
        return result.scalar_one_or_none()

    async def list_by_project(
        self,
        project_id: str,
        limit: int = 20,
        cursor: str | None = None,
    ) -> tuple[list[Aggregation], str | None]:
        """List aggregations by project with cursor pagination"""
        query = (
            select(Aggregation)
            .where(Aggregation.project_id == project_id)
            .order_by(Aggregation.created_at.desc())
        )

        if cursor:
            cursor_agg = await self.get_by_id(cursor)
            if cursor_agg:
                query = query.where(Aggregation.created_at < cursor_agg.created_at)

        query = query.limit(limit + 1)
        result = await self.session.execute(query)
        aggregations = list(result.scalars().all())

        next_cursor = None
        if len(aggregations) > limit:
            aggregations = aggregations[:limit]
            next_cursor = aggregations[-1].aggregation_id

        return aggregations, next_cursor

    async def delete(self, aggregation_id: str) -> bool:
        """Delete an aggregation and its members"""
        agg = await self.get_by_id(aggregation_id)
        if not agg:
            return False
        await self.session.delete(agg)
        await self.session.flush()
        return True

    async def member_count(self, aggregation_id: str) -> int:
        """Count members of an aggregation"""
        result = await self.session.execute(
            select(func.count()).where(
                AggregationMember.aggregation_id == aggregation_id
            )
        )
        return result.scalar_one()

    # ── Member CRUD ───────────────────────────────────────────

    async def add_member(
        self, aggregation_id: str, data: AggregationMemberAdd
    ) -> AggregationMember:
        """Add a run to an aggregation"""
        member = AggregationMember(
            member_id=generate_id(),
            aggregation_id=aggregation_id,
            run_id=data.run_id,
            metadata_json=json.dumps(data.metadata),
            added_at=utc_now(),
        )
        self.session.add(member)
        await self.session.flush()
        return member

    async def remove_member(self, aggregation_id: str, run_id: str) -> bool:
        """Remove a run from an aggregation"""
        result = await self.session.execute(
            delete(AggregationMember).where(
                AggregationMember.aggregation_id == aggregation_id,
                AggregationMember.run_id == run_id,
            )
        )
        rowcount = getattr(result, "rowcount", 0)
        return bool(rowcount)

    async def list_members(
        self,
        aggregation_id: str,
        limit: int = 100,
        cursor: str | None = None,
    ) -> tuple[list[AggregationMember], str | None]:
        """List members of an aggregation with cursor pagination"""
        query = (
            select(AggregationMember)
            .where(AggregationMember.aggregation_id == aggregation_id)
            .order_by(AggregationMember.added_at.desc())
        )

        if cursor:
            cursor_member = await self.session.execute(
                select(AggregationMember).where(AggregationMember.member_id == cursor)
            )
            cursor_obj = cursor_member.scalar_one_or_none()
            if cursor_obj:
                query = query.where(AggregationMember.added_at < cursor_obj.added_at)

        query = query.limit(limit + 1)
        result = await self.session.execute(query)
        members = list(result.scalars().all())

        next_cursor = None
        if len(members) > limit:
            members = members[:limit]
            next_cursor = members[-1].member_id

        return members, next_cursor

    async def get_member_run_ids(self, aggregation_id: str) -> list[str]:
        """Get all run IDs in an aggregation (for metric queries)"""
        result = await self.session.execute(
            select(AggregationMember.run_id).where(
                AggregationMember.aggregation_id == aggregation_id
            )
        )
        return list(result.scalars().all())
