"""Comparison Indicator repository"""

import json
from typing import Any

from axion_lab_server.repos.models.entities import (
    AggregationMember,
    ComparisonIndicator,
    Run,
)
from axion_lab_server.shared.libs import generate_id, utc_now
from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession


class ComparisonIndicatorRepository:
    """Repository for ComparisonIndicator operations"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert(
        self,
        run_id: str,
        key: str,
        value: Any,
        baseline_ref: str | None = None,
        version: int = 1,
    ) -> ComparisonIndicator:
        """Upsert a comparison indicator (insert or update)"""
        existing = await self.get_by_run_and_key(run_id, key, version)

        if existing:
            existing.value_json = json.dumps(value)
            existing.baseline_ref = baseline_ref
            existing.computed_at = utc_now()
            await self.session.flush()
            return existing

        ci = ComparisonIndicator(
            ci_id=generate_id(),
            run_id=run_id,
            key=key,
            value_json=json.dumps(value),
            baseline_ref=baseline_ref,
            computed_at=utc_now(),
            version=version,
        )
        self.session.add(ci)
        await self.session.flush()
        return ci

    async def get_by_run_and_key(
        self, run_id: str, key: str, version: int = 1
    ) -> ComparisonIndicator | None:
        """Get comparison indicator by run ID and key"""
        result = await self.session.execute(
            select(ComparisonIndicator).where(
                and_(
                    ComparisonIndicator.run_id == run_id,
                    ComparisonIndicator.key == key,
                    ComparisonIndicator.version == version,
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_by_run(self, run_id: str) -> list[ComparisonIndicator]:
        """List comparison indicators by run"""
        result = await self.session.execute(
            select(ComparisonIndicator)
            .where(ComparisonIndicator.run_id == run_id)
            .order_by(ComparisonIndicator.computed_at.desc())
        )
        return list(result.scalars().all())

    async def list_by_batch(
        self,
        batch_id: str,
        key: str | None = None,
        limit: int = 100,
        cursor: str | None = None,
    ) -> tuple[list[ComparisonIndicator], str | None]:
        """List comparison indicators by batch with optional key filter"""
        query = (
            select(ComparisonIndicator)
            .join(Run, ComparisonIndicator.run_id == Run.run_id)
            .where(Run.batch_id == batch_id)
        )

        if key:
            query = query.where(ComparisonIndicator.key == key)

        query = query.order_by(ComparisonIndicator.computed_at.desc())

        if cursor:
            cursor_ci = await self.session.execute(
                select(ComparisonIndicator).where(ComparisonIndicator.ci_id == cursor)
            )
            cursor_obj = cursor_ci.scalar_one_or_none()
            if cursor_obj:
                query = query.where(
                    ComparisonIndicator.computed_at < cursor_obj.computed_at
                )

        query = query.limit(limit + 1)
        result = await self.session.execute(query)
        indicators = list(result.scalars().all())

        next_cursor = None
        if len(indicators) > limit:
            indicators = indicators[:limit]
            next_cursor = indicators[-1].ci_id

        return indicators, next_cursor

    async def delete_by_run(self, run_id: str) -> int:
        """Delete all comparison indicators for a run"""
        result = await self.session.execute(
            delete(ComparisonIndicator).where(ComparisonIndicator.run_id == run_id)
        )
        rowcount = getattr(result, "rowcount", 0)
        return int(rowcount or 0)

    async def list_by_aggregation(
        self,
        aggregation_id: str,
        key: str | None = None,
        limit: int = 100,
        cursor: str | None = None,
    ) -> tuple[list[ComparisonIndicator], str | None]:
        """List comparison indicators for runs in an aggregation"""
        query = (
            select(ComparisonIndicator)
            .join(
                AggregationMember,
                ComparisonIndicator.run_id == AggregationMember.run_id,
            )
            .where(AggregationMember.aggregation_id == aggregation_id)
        )

        if key:
            query = query.where(ComparisonIndicator.key == key)

        query = query.order_by(ComparisonIndicator.computed_at.desc())

        if cursor:
            cursor_ci = await self.session.execute(
                select(ComparisonIndicator).where(ComparisonIndicator.ci_id == cursor)
            )
            cursor_obj = cursor_ci.scalar_one_or_none()
            if cursor_obj:
                query = query.where(
                    ComparisonIndicator.computed_at < cursor_obj.computed_at
                )

        query = query.limit(limit + 1)
        result = await self.session.execute(query)
        indicators = list(result.scalars().all())

        next_cursor = None
        if len(indicators) > limit:
            indicators = indicators[:limit]
            next_cursor = indicators[-1].ci_id

        return indicators, next_cursor
