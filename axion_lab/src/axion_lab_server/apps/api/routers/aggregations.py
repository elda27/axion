"""Aggregation API router"""

import json

from fastapi import APIRouter, status

from axion_lab_server.apps.api.deps import (
    AggregationPath,
    AggregationRepo,
    ArtifactRepo,
    CIRepo,
    ProjectPath,
    RMRepo,
)
from axion_lab_server.shared.domain import (
    AggregationCreate,
    AggregationMemberAdd,
    AggregationMemberResponse,
    AggregationResponse,
    ComparisonIndicatorResponse,
    CursorPaginatedResponse,
    RunMetricResponse,
)

router = APIRouter(tags=["Aggregations"])


def _build_aggregation_response(agg, *, member_count: int = 0) -> AggregationResponse:
    """Build aggregation response from ORM entity"""
    return AggregationResponse(
        aggregationId=agg.aggregation_id,
        projectId=agg.project_id,
        name=agg.name,
        description=agg.description,
        groupByKeys=json.loads(agg.group_by_keys_json),
        filter=json.loads(agg.filter_json),
        createdAt=agg.created_at,
        memberCount=member_count,
    )


def _build_member_response(member) -> AggregationMemberResponse:
    """Build aggregation member response from ORM entity"""
    return AggregationMemberResponse(
        memberId=member.member_id,
        aggregationId=member.aggregation_id,
        runId=member.run_id,
        metadata=json.loads(member.metadata_json),
        addedAt=member.added_at,
    )


# ── Aggregation CRUD ──────────────────────────────────────────


@router.post(
    "/projects/{project_id}/aggregations",
    response_model=AggregationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_aggregation(
    data: AggregationCreate,
    project: ProjectPath,
    repo: AggregationRepo,
) -> AggregationResponse:
    """Create a new aggregation in a project"""
    agg = await repo.create(project.project_id, data)
    return _build_aggregation_response(agg, member_count=0)


@router.get(
    "/projects/{project_id}/aggregations",
    response_model=CursorPaginatedResponse[AggregationResponse],
)
async def list_aggregations(
    project: ProjectPath,
    repo: AggregationRepo,
    limit: int = 20,
    cursor: str | None = None,
) -> CursorPaginatedResponse[AggregationResponse]:
    """List aggregations in a project"""
    aggregations, next_cursor = await repo.list_by_project(
        project.project_id, limit=limit, cursor=cursor
    )
    items = []
    for agg in aggregations:
        count = await repo.member_count(agg.aggregation_id)
        items.append(_build_aggregation_response(agg, member_count=count))
    return CursorPaginatedResponse(
        items=items,
        next_cursor=next_cursor,
        has_more=next_cursor is not None,
    )


@router.get(
    "/aggregations/{aggregation_id}",
    response_model=AggregationResponse,
)
async def get_aggregation(
    aggregation: AggregationPath,
    repo: AggregationRepo,
) -> AggregationResponse:
    """Get aggregation by ID"""
    count = await repo.member_count(aggregation.aggregation_id)
    return _build_aggregation_response(aggregation, member_count=count)


@router.delete(
    "/aggregations/{aggregation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_aggregation(
    aggregation: AggregationPath,
    repo: AggregationRepo,
) -> None:
    """Delete an aggregation"""
    await repo.delete(aggregation.aggregation_id)


# ── Member management ─────────────────────────────────────────


@router.post(
    "/aggregations/{aggregation_id}/members",
    response_model=AggregationMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_member(
    data: AggregationMemberAdd,
    aggregation: AggregationPath,
    repo: AggregationRepo,
) -> AggregationMemberResponse:
    """Add a run to an aggregation"""
    member = await repo.add_member(aggregation.aggregation_id, data)
    return _build_member_response(member)


@router.get(
    "/aggregations/{aggregation_id}/members",
    response_model=CursorPaginatedResponse[AggregationMemberResponse],
)
async def list_members(
    aggregation: AggregationPath,
    repo: AggregationRepo,
    limit: int = 100,
    cursor: str | None = None,
) -> CursorPaginatedResponse[AggregationMemberResponse]:
    """List members of an aggregation"""
    members, next_cursor = await repo.list_members(
        aggregation.aggregation_id, limit=limit, cursor=cursor
    )
    return CursorPaginatedResponse(
        items=[_build_member_response(m) for m in members],
        next_cursor=next_cursor,
        has_more=next_cursor is not None,
    )


@router.delete(
    "/aggregations/{aggregation_id}/members/{run_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_member(
    aggregation: AggregationPath,
    run_id: str,
    repo: AggregationRepo,
) -> None:
    """Remove a run from an aggregation"""
    await repo.remove_member(aggregation.aggregation_id, run_id)


# ── Metrics across aggregation members ────────────────────────


from axion_lab_server.apps.api.routers.run_metrics import (
    _build_rm_response,
    _get_evaluation_types_by_run,
)


def _build_ci_response(ci) -> ComparisonIndicatorResponse:
    """Build comparison indicator response"""
    value = json.loads(ci.value_json) if ci.value_json else None
    return ComparisonIndicatorResponse(
        ciId=ci.ci_id,
        runId=ci.run_id,
        key=ci.key,
        value=value,
        baselineRef=ci.baseline_ref,
        computedAt=ci.computed_at,
        version=ci.version,
    )


@router.get(
    "/aggregations/{aggregation_id}/run-metrics",
    response_model=CursorPaginatedResponse[RunMetricResponse],
)
async def list_run_metrics_by_aggregation(
    aggregation: AggregationPath,
    repo: RMRepo,
    artifact_repo: ArtifactRepo,
    key: str | None = None,
    limit: int = 100,
    cursor: str | None = None,
) -> CursorPaginatedResponse[RunMetricResponse]:
    """List run metrics for all runs in an aggregation"""
    metrics, next_cursor = await repo.list_by_aggregation(
        aggregation.aggregation_id, key=key, limit=limit, cursor=cursor
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


@router.get(
    "/aggregations/{aggregation_id}/comparison-indicators",
    response_model=CursorPaginatedResponse[ComparisonIndicatorResponse],
)
async def list_comparison_indicators_by_aggregation(
    aggregation: AggregationPath,
    repo: CIRepo,
    key: str | None = None,
    limit: int = 100,
    cursor: str | None = None,
) -> CursorPaginatedResponse[ComparisonIndicatorResponse]:
    """List comparison indicators for all runs in an aggregation"""
    indicators, next_cursor = await repo.list_by_aggregation(
        aggregation.aggregation_id, key=key, limit=limit, cursor=cursor
    )
    return CursorPaginatedResponse(
        items=[_build_ci_response(ci) for ci in indicators],
        next_cursor=next_cursor,
        has_more=next_cursor is not None,
    )
