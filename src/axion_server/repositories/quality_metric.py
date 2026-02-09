"""Quality Metric repository"""

import json
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from axion.schemas.quality_metric import QualityMetricSource
from axion_server.models.entities import QualityMetric
from axion_server.repositories.base import generate_id, utc_now


class QualityMetricRepository:
    """Repository for QualityMetric operations"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert(
        self,
        run_id: str,
        key: str,
        value: Any,
        source: QualityMetricSource,
        version: int = 1,
    ) -> QualityMetric:
        """Upsert a quality metric (insert or update)"""
        # Check if exists
        existing = await self.get_by_run_and_key(run_id, key, version)

        if existing:
            existing.value_json = json.dumps(value)
            existing.source = source.value
            existing.computed_at = utc_now()
            await self.session.flush()
            return existing

        qm = QualityMetric(
            qm_id=generate_id(),
            run_id=run_id,
            key=key,
            value_json=json.dumps(value),
            source=source.value,
            computed_at=utc_now(),
            version=version,
        )
        self.session.add(qm)
        await self.session.flush()
        return qm

    async def get_by_run_and_key(
        self, run_id: str, key: str, version: int = 1
    ) -> QualityMetric | None:
        """Get quality metric by run ID and key"""
        result = await self.session.execute(
            select(QualityMetric).where(
                and_(
                    QualityMetric.run_id == run_id,
                    QualityMetric.key == key,
                    QualityMetric.version == version,
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_by_run(self, run_id: str) -> list[QualityMetric]:
        """List quality metrics by run"""
        result = await self.session.execute(
            select(QualityMetric)
            .where(QualityMetric.run_id == run_id)
            .order_by(QualityMetric.computed_at.desc())
        )
        return list(result.scalars().all())

    async def list_by_batch(
        self,
        batch_id: str,
        key: str | None = None,
        limit: int = 100,
        cursor: str | None = None,
    ) -> tuple[list[QualityMetric], str | None]:
        """List quality metrics by batch with optional key filter"""
        from axion_server.models.entities import Run

        query = (
            select(QualityMetric)
            .join(Run, QualityMetric.run_id == Run.run_id)
            .where(Run.batch_id == batch_id)
        )

        if key:
            query = query.where(QualityMetric.key == key)

        query = query.order_by(QualityMetric.computed_at.desc())

        if cursor:
            cursor_qm = await self.session.execute(
                select(QualityMetric).where(QualityMetric.qm_id == cursor)
            )
            cursor_obj = cursor_qm.scalar_one_or_none()
            if cursor_obj:
                query = query.where(QualityMetric.computed_at < cursor_obj.computed_at)

        query = query.limit(limit + 1)
        result = await self.session.execute(query)
        metrics = list(result.scalars().all())

        next_cursor = None
        if len(metrics) > limit:
            metrics = metrics[:limit]
            next_cursor = metrics[-1].qm_id

        return metrics, next_cursor

    async def delete_by_run(self, run_id: str) -> int:
        """Delete all quality metrics for a run"""
        from sqlalchemy import delete

        result = await self.session.execute(
            delete(QualityMetric).where(QualityMetric.run_id == run_id)
        )
        return result.rowcount
