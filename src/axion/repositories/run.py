"""Run repository"""

import json

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from axion.models.entities import Run, RunPin
from axion.repositories.base import generate_id, utc_now
from axion.schemas.run import RunCreate, RunStatus, RunUpdate


class RunRepository:
    """Repository for Run operations"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, batch_id: str, data: RunCreate) -> Run:
        """Create a new run"""
        now = utc_now()
        run = Run(
            run_id=generate_id(),
            batch_id=batch_id,
            name=data.name,
            status=data.status.value,
            tags_json=json.dumps(data.tags),
            note=data.note,
            created_at=now,
            updated_at=now,
        )
        self.session.add(run)
        await self.session.flush()
        return run

    async def get_by_id(self, run_id: str) -> Run | None:
        """Get run by ID"""
        result = await self.session.execute(select(Run).where(Run.run_id == run_id))
        return result.scalar_one_or_none()

    async def get_by_id_with_pins(self, run_id: str) -> Run | None:
        """Get run by ID with pins loaded"""
        result = await self.session.execute(
            select(Run).where(Run.run_id == run_id).options(selectinload(Run.pins))
        )
        return result.scalar_one_or_none()

    async def update(self, run_id: str, data: RunUpdate) -> Run | None:
        """Update a run"""
        run = await self.get_by_id(run_id)
        if not run:
            return None

        if data.name is not None:
            run.name = data.name
        if data.status is not None:
            run.status = data.status.value
        if data.tags is not None:
            run.tags_json = json.dumps(data.tags)
        if data.note is not None:
            run.note = data.note
        run.updated_at = utc_now()

        await self.session.flush()
        return run

    async def list_by_batch(
        self,
        batch_id: str,
        status: RunStatus | None = None,
        include_garbage: bool = False,
        tag: str | None = None,
        q: str | None = None,
        limit: int = 20,
        cursor: str | None = None,
    ) -> tuple[list[Run], str | None]:
        """List runs by batch with filtering and cursor pagination"""
        query = select(Run).where(Run.batch_id == batch_id)

        # Filter by status
        if status:
            query = query.where(Run.status == status.value)
        elif not include_garbage:
            query = query.where(Run.status != RunStatus.GARBAGE.value)

        # Filter by tag (substring match in JSON array)
        if tag:
            query = query.where(Run.tags_json.contains(f'"{tag}"'))

        # Search by name
        if q:
            query = query.where(Run.name.ilike(f"%{q}%"))

        query = query.order_by(Run.created_at.desc())

        if cursor:
            cursor_run = await self.get_by_id(cursor)
            if cursor_run:
                query = query.where(Run.created_at < cursor_run.created_at)

        query = query.limit(limit + 1)
        result = await self.session.execute(query)
        runs = list(result.scalars().all())

        next_cursor = None
        if len(runs) > limit:
            runs = runs[:limit]
            next_cursor = runs[-1].run_id

        return runs, next_cursor

    async def get_champion(self, batch_id: str) -> Run | None:
        """Get champion run for a batch"""
        result = await self.session.execute(
            select(Run)
            .join(RunPin, Run.run_id == RunPin.run_id)
            .where(
                and_(
                    RunPin.batch_id == batch_id,
                    RunPin.pin_type == "champion",
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_user_selected(self, batch_id: str) -> list[Run]:
        """Get user selected runs for a batch"""
        result = await self.session.execute(
            select(Run)
            .join(RunPin, Run.run_id == RunPin.run_id)
            .where(
                and_(
                    RunPin.batch_id == batch_id,
                    RunPin.pin_type == "user_selected",
                )
            )
            .order_by(RunPin.pinned_at.desc())
        )
        return list(result.scalars().all())

    async def get_recent(
        self, batch_id: str, limit: int = 3, exclude_ids: list[str] | None = None
    ) -> list[Run]:
        """Get recent active runs for a batch"""
        query = (
            select(Run)
            .where(
                and_(
                    Run.batch_id == batch_id,
                    Run.status == RunStatus.ACTIVE.value,
                )
            )
            .order_by(Run.created_at.desc())
        )

        if exclude_ids:
            query = query.where(Run.run_id.notin_(exclude_ids))

        query = query.limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_active_for_dp(
        self, batch_id: str, include_garbage: bool = False
    ) -> list[Run]:
        """List runs for DP processing"""
        query = select(Run).where(Run.batch_id == batch_id)

        if not include_garbage:
            query = query.where(Run.status != RunStatus.GARBAGE.value)

        query = query.order_by(Run.created_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())
