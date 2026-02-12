"""DP Job repository"""

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from axion_server.repos.models.entities import DPJob
from axion_server.shared.domain import DPJobCreate, DPJobStatus
from axion_server.shared.libs import generate_id, utc_now


class DPJobRepository:
    """Repository for DPJob operations"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self, batch_id: str, data: DPJobCreate, requested_by: str | None = None
    ) -> DPJob:
        """Create a new DP job"""
        job = DPJob(
            job_id=generate_id(),
            batch_id=batch_id,
            mode=data.mode.value,
            recompute=1 if data.recompute else 0,
            status=DPJobStatus.QUEUED.value,
            requested_by=requested_by,
            created_at=utc_now(),
        )
        self.session.add(job)
        await self.session.flush()
        return job

    async def get_by_id(self, job_id: str) -> DPJob | None:
        """Get DP job by ID"""
        result = await self.session.execute(select(DPJob).where(DPJob.job_id == job_id))
        return result.scalar_one_or_none()

    async def update_status(
        self,
        job_id: str,
        status: DPJobStatus,
        error_text: str | None = None,
    ) -> DPJob | None:
        """Update DP job status"""
        job = await self.get_by_id(job_id)
        if not job:
            return None

        now = utc_now()
        job.status = status.value

        if status == DPJobStatus.RUNNING:
            job.started_at = now
        elif status in (
            DPJobStatus.SUCCEEDED,
            DPJobStatus.FAILED,
            DPJobStatus.CANCELED,
        ):
            job.finished_at = now
            if error_text:
                job.error_text = error_text

        await self.session.flush()
        return job

    async def has_running_job(self, batch_id: str) -> bool:
        """Check if batch has a running job"""
        result = await self.session.execute(
            select(DPJob).where(
                and_(
                    DPJob.batch_id == batch_id,
                    DPJob.status == DPJobStatus.RUNNING.value,
                )
            )
        )
        return result.scalar_one_or_none() is not None

    async def list_by_batch(
        self, batch_id: str, limit: int = 20, cursor: str | None = None
    ) -> tuple[list[DPJob], str | None]:
        """List DP jobs by batch with cursor pagination"""
        query = (
            select(DPJob)
            .where(DPJob.batch_id == batch_id)
            .order_by(DPJob.created_at.desc())
        )

        if cursor:
            cursor_job = await self.get_by_id(cursor)
            if cursor_job:
                query = query.where(DPJob.created_at < cursor_job.created_at)

        query = query.limit(limit + 1)
        result = await self.session.execute(query)
        jobs = list(result.scalars().all())

        next_cursor = None
        if len(jobs) > limit:
            jobs = jobs[:limit]
            next_cursor = jobs[-1].job_id

        return jobs, next_cursor
