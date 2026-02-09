"""Artifact repository"""

import json
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from axion.schemas.artifact import ArtifactCreate, ArtifactKind
from axion_server.models.entities import Artifact
from axion_server.repositories.base import generate_id, utc_now


class ArtifactRepository:
    """Repository for Artifact operations"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, run_id: str, data: ArtifactCreate) -> Artifact:
        """Create a new artifact"""
        payload_text: str | None = None
        payload_number: float | None = None

        if data.kind == ArtifactKind.INLINE_NUMBER:
            payload_number = float(data.payload)
        elif data.kind == ArtifactKind.INLINE_JSON:
            payload_text = json.dumps(data.payload)
        else:
            payload_text = str(data.payload)

        artifact = Artifact(
            artifact_id=generate_id(),
            run_id=run_id,
            kind=data.kind.value,
            type=data.type,
            label=data.label,
            payload_text=payload_text,
            payload_number=payload_number,
            meta_json=json.dumps(data.meta),
            created_at=utc_now(),
        )
        self.session.add(artifact)
        await self.session.flush()
        return artifact

    async def get_by_id(self, artifact_id: str) -> Artifact | None:
        """Get artifact by ID"""
        result = await self.session.execute(
            select(Artifact).where(Artifact.artifact_id == artifact_id)
        )
        return result.scalar_one_or_none()

    async def list_by_run(
        self, run_id: str, limit: int = 100, cursor: str | None = None
    ) -> tuple[list[Artifact], str | None]:
        """List artifacts by run with cursor pagination"""
        query = (
            select(Artifact)
            .where(Artifact.run_id == run_id)
            .order_by(Artifact.created_at.desc())
        )

        if cursor:
            cursor_artifact = await self.get_by_id(cursor)
            if cursor_artifact:
                query = query.where(Artifact.created_at < cursor_artifact.created_at)

        query = query.limit(limit + 1)
        result = await self.session.execute(query)
        artifacts = list(result.scalars().all())

        next_cursor = None
        if len(artifacts) > limit:
            artifacts = artifacts[:limit]
            next_cursor = artifacts[-1].artifact_id

        return artifacts, next_cursor

    async def list_by_run_and_type(
        self, run_id: str, artifact_type: str
    ) -> list[Artifact]:
        """List artifacts by run and type"""
        result = await self.session.execute(
            select(Artifact)
            .where(Artifact.run_id == run_id, Artifact.type == artifact_type)
            .order_by(Artifact.created_at.desc())
        )
        return list(result.scalars().all())

    async def delete(self, artifact_id: str) -> bool:
        """Delete an artifact"""
        result = await self.session.execute(
            delete(Artifact).where(Artifact.artifact_id == artifact_id)
        )
        return result.rowcount > 0

    def get_payload(self, artifact: Artifact) -> Any:
        """Get artifact payload in appropriate type"""
        if artifact.kind == ArtifactKind.INLINE_NUMBER.value:
            return artifact.payload_number
        elif artifact.kind == ArtifactKind.INLINE_JSON.value:
            return json.loads(artifact.payload_text) if artifact.payload_text else None
        else:
            return artifact.payload_text
