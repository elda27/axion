"""Run Metrics API router"""

import json

from axion_lab_server.apps.api.deps import ArtifactRepo, BatchPath, RMRepo, RunPath
from axion_lab_server.repos.models.entities import Artifact
from axion_lab_server.shared.domain import CursorPaginatedResponse, RunMetricResponse
from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["Run Metrics"])


def _build_rm_response(
    rm, *, evaluation_types: list[str] | None = None
) -> RunMetricResponse:
    """Build run metric response"""
    value = json.loads(rm.value_json) if rm.value_json else None
    return RunMetricResponse(
        qmId=rm.qm_id,
        runId=rm.run_id,
        key=rm.key,
        value=value,
        source=rm.source,
        evaluationTypes=evaluation_types or [],
        computedAt=rm.computed_at,
        version=rm.version,
    )


async def _get_evaluation_types_by_run(
    session: AsyncSession, run_ids: list[str]
) -> dict[str, list[str]]:
    """Get distinct artifact types per run_id by querying artifacts table."""
    if not run_ids:
        return {}
    result = await session.execute(
        select(Artifact.run_id, Artifact.type)
        .where(Artifact.run_id.in_(run_ids))
        .distinct()
        .order_by(Artifact.run_id, Artifact.type)
    )
    mapping: dict[str, list[str]] = {}
    for run_id, artifact_type in result:
        mapping.setdefault(run_id, []).append(artifact_type)
    return mapping


@router.get(
    "/runs/{run_id}/run-metrics",
    response_model=list[RunMetricResponse],
)
async def list_run_metrics_by_run(
    run: RunPath,
    repo: RMRepo,
    artifact_repo: ArtifactRepo,
) -> list[RunMetricResponse]:
    """List run metrics for a run"""
    metrics = await repo.list_by_run(run.run_id)
    type_map = await _get_evaluation_types_by_run(artifact_repo.session, [run.run_id])
    eval_types = type_map.get(run.run_id, [])
    return [_build_rm_response(m, evaluation_types=eval_types) for m in metrics]


@router.get(
    "/batches/{batch_id}/run-metrics",
    response_model=CursorPaginatedResponse[RunMetricResponse],
)
async def list_run_metrics_by_batch(
    batch: BatchPath,
    repo: RMRepo,
    artifact_repo: ArtifactRepo,
    key: str | None = None,
    limit: int = 100,
    cursor: str | None = None,
) -> CursorPaginatedResponse[RunMetricResponse]:
    """List run metrics for a batch"""
    metrics, next_cursor = await repo.list_by_batch(
        batch.batch_id, key=key, limit=limit, cursor=cursor
    )
    run_ids = list({m.run_id for m in metrics})
    type_map = await _get_evaluation_types_by_run(artifact_repo.session, run_ids)
    return CursorPaginatedResponse(
        items=[
            _build_rm_response(m, evaluation_types=type_map.get(m.run_id, []))
            for m in metrics
        ],
        next_cursor=next_cursor,
        has_more=next_cursor is not None,
    )
