"""Run Metric repository"""

import json
from typing import Any

from axion_lab_server.repos.models.entities import AggregationMember, Run, RunMetric
from axion_lab_server.shared.domain import RunMetricSource
from axion_lab_server.shared.libs import generate_id, utc_now
from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession


class RunMetricRepository:
    """Repository for RunMetric operations"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert(
        self,
        run_id: str,
        key: str,
        value: Any,
        source: RunMetricSource,
        version: int = 1,
    ) -> RunMetric:
        """Upsert a run metric (insert or update)"""
        # Check if exists
        existing = await self.get_by_run_and_key(run_id, key, version)

        if existing:
            existing.value_json = json.dumps(value)
            existing.source = source.value
            existing.computed_at = utc_now()
            await self.session.flush()
            return existing

        rm = RunMetric(
            qm_id=generate_id(),
            run_id=run_id,
            key=key,
            value_json=json.dumps(value),
            source=source.value,
            computed_at=utc_now(),
            version=version,
        )
        self.session.add(rm)
        await self.session.flush()
        return rm

    async def get_by_run_and_key(
        self, run_id: str, key: str, version: int = 1
    ) -> RunMetric | None:
        """Get run metric by run ID and key"""
        result = await self.session.execute(
            select(RunMetric).where(
                and_(
                    RunMetric.run_id == run_id,
                    RunMetric.key == key,
                    RunMetric.version == version,
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_by_run(self, run_id: str) -> list[RunMetric]:
        """List run metrics by run"""
        result = await self.session.execute(
            select(RunMetric)
            .where(RunMetric.run_id == run_id)
            .order_by(RunMetric.computed_at.desc())
        )
        return list(result.scalars().all())

    async def list_by_batch(
        self,
        batch_id: str,
        key: str | None = None,
        limit: int = 100,
        cursor: str | None = None,
    ) -> tuple[list[RunMetric], str | None]:
        """List run metrics by batch with optional key filter"""
        query = (
            select(RunMetric)
            .join(Run, RunMetric.run_id == Run.run_id)
            .where(Run.batch_id == batch_id)
        )

        if key:
            query = query.where(RunMetric.key == key)

        query = query.order_by(RunMetric.computed_at.desc())

        if cursor:
            cursor_rm = await self.session.execute(
                select(RunMetric).where(RunMetric.qm_id == cursor)
            )
            cursor_obj = cursor_rm.scalar_one_or_none()
            if cursor_obj:
                query = query.where(RunMetric.computed_at < cursor_obj.computed_at)

        query = query.limit(limit + 1)
        result = await self.session.execute(query)
        metrics = list(result.scalars().all())

        next_cursor = None
        if len(metrics) > limit:
            metrics = metrics[:limit]
            next_cursor = metrics[-1].qm_id

        return metrics, next_cursor

    async def delete_by_run(self, run_id: str) -> int:
        """Delete all run metrics for a run"""
        result = await self.session.execute(
            delete(RunMetric).where(RunMetric.run_id == run_id)
        )
        rowcount = getattr(result, "rowcount", 0)
        return int(rowcount or 0)

    async def list_by_aggregation(
        self,
        aggregation_id: str,
        key: str | None = None,
        limit: int = 100,
        cursor: str | None = None,
    ) -> tuple[list[RunMetric], str | None]:
        """List run metrics for runs in an aggregation"""
        query = (
            select(RunMetric)
            .join(
                AggregationMember,
                RunMetric.run_id == AggregationMember.run_id,
            )
            .where(AggregationMember.aggregation_id == aggregation_id)
        )

        if key:
            query = query.where(RunMetric.key == key)

        query = query.order_by(RunMetric.computed_at.desc())

        if cursor:
            cursor_rm = await self.session.execute(
                select(RunMetric).where(RunMetric.qm_id == cursor)
            )
            cursor_obj = cursor_rm.scalar_one_or_none()
            if cursor_obj:
                query = query.where(RunMetric.computed_at < cursor_obj.computed_at)

        query = query.limit(limit + 1)
        result = await self.session.execute(query)
        metrics = list(result.scalars().all())

        next_cursor = None
        if len(metrics) > limit:
            metrics = metrics[:limit]
            next_cursor = metrics[-1].qm_id

        return metrics, next_cursor
