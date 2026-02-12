"""Run Pin repository"""

from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from axion_server.repos.models.entities import RunPin
from axion_server.shared.domain import PinType
from axion_server.shared.libs import generate_id, utc_now


class RunPinRepository:
    """Repository for RunPin operations"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        run_id: str,
        batch_id: str,
        pin_type: PinType,
        pinned_by: str | None = None,
    ) -> RunPin:
        """Create a new pin (with upsert for champion)"""
        # If champion, remove existing champion first
        if pin_type == PinType.CHAMPION:
            await self.delete_champion(batch_id)

        pin = RunPin(
            pin_id=generate_id(),
            run_id=run_id,
            batch_id=batch_id,
            pin_type=pin_type.value,
            pinned_by=pinned_by,
            pinned_at=utc_now(),
        )
        self.session.add(pin)
        await self.session.flush()
        return pin

    async def get_by_run_and_type(
        self, run_id: str, pin_type: PinType
    ) -> RunPin | None:
        """Get pin by run ID and type"""
        result = await self.session.execute(
            select(RunPin).where(
                and_(
                    RunPin.run_id == run_id,
                    RunPin.pin_type == pin_type.value,
                )
            )
        )
        return result.scalar_one_or_none()

    async def delete_by_run_and_type(self, run_id: str, pin_type: PinType) -> bool:
        """Delete pin by run ID and type"""
        result = await self.session.execute(
            delete(RunPin).where(
                and_(
                    RunPin.run_id == run_id,
                    RunPin.pin_type == pin_type.value,
                )
            )
        )
        rowcount = getattr(result, "rowcount", 0)
        return int(rowcount or 0) > 0

    async def delete_champion(self, batch_id: str) -> bool:
        """Delete champion pin for a batch"""
        result = await self.session.execute(
            delete(RunPin).where(
                and_(
                    RunPin.batch_id == batch_id,
                    RunPin.pin_type == PinType.CHAMPION.value,
                )
            )
        )
        rowcount = getattr(result, "rowcount", 0)
        return int(rowcount or 0) > 0

    async def get_champion_run_id(self, batch_id: str) -> str | None:
        """Get champion run ID for a batch"""
        result = await self.session.execute(
            select(RunPin.run_id).where(
                and_(
                    RunPin.batch_id == batch_id,
                    RunPin.pin_type == PinType.CHAMPION.value,
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_by_batch(self, batch_id: str) -> list[RunPin]:
        """List all pins for a batch"""
        result = await self.session.execute(
            select(RunPin)
            .where(RunPin.batch_id == batch_id)
            .order_by(RunPin.pinned_at.desc())
        )
        return list(result.scalars().all())
