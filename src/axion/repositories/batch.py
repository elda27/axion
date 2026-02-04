"""Batch repository"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from axion.models.entities import Batch
from axion.repositories.base import generate_id, utc_now
from axion.schemas.batch import BatchCreate


class BatchRepository:
    """Repository for Batch operations"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, project_id: str, data: BatchCreate) -> Batch:
        """Create a new batch"""
        batch = Batch(
            batch_id=generate_id(),
            project_id=project_id,
            name=data.name,
            created_at=utc_now(),
        )
        self.session.add(batch)
        await self.session.flush()
        return batch

    async def get_by_id(self, batch_id: str) -> Batch | None:
        """Get batch by ID"""
        result = await self.session.execute(
            select(Batch).where(Batch.batch_id == batch_id)
        )
        return result.scalar_one_or_none()

    async def list_by_project(
        self, project_id: str, limit: int = 20, cursor: str | None = None
    ) -> tuple[list[Batch], str | None]:
        """List batches by project with cursor pagination"""
        query = (
            select(Batch)
            .where(Batch.project_id == project_id)
            .order_by(Batch.created_at.desc())
        )

        if cursor:
            cursor_batch = await self.get_by_id(cursor)
            if cursor_batch:
                query = query.where(Batch.created_at < cursor_batch.created_at)

        query = query.limit(limit + 1)
        result = await self.session.execute(query)
        batches = list(result.scalars().all())

        next_cursor = None
        if len(batches) > limit:
            batches = batches[:limit]
            next_cursor = batches[-1].batch_id

        return batches, next_cursor
