"""Common API dependencies"""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from axion_lab_server.repos import (
    AggregationRepository,
    ArtifactRepository,
    BatchRepository,
    ComparisonIndicatorRepository,
    DPJobRepository,
    OrgRepository,
    ProjectRepository,
    RunMetricRepository,
    RunPinRepository,
    RunRepository,
)
from axion_lab_server.repos.models.entities import Aggregation, Batch, Org, Project, Run
from axion_lab_server.shared.kernel import get_db

# Database session dependency
DBSession = Annotated[AsyncSession, Depends(get_db)]


# Repository dependencies
async def get_org_repo(session: DBSession) -> AsyncGenerator[OrgRepository, None]:
    yield OrgRepository(session)


async def get_project_repo(
    session: DBSession,
) -> AsyncGenerator[ProjectRepository, None]:
    yield ProjectRepository(session)


async def get_batch_repo(session: DBSession) -> AsyncGenerator[BatchRepository, None]:
    yield BatchRepository(session)


async def get_aggregation_repo(
    session: DBSession,
) -> AsyncGenerator[AggregationRepository, None]:
    yield AggregationRepository(session)


async def get_run_repo(session: DBSession) -> AsyncGenerator[RunRepository, None]:
    yield RunRepository(session)


async def get_run_pin_repo(
    session: DBSession,
) -> AsyncGenerator[RunPinRepository, None]:
    yield RunPinRepository(session)


async def get_artifact_repo(
    session: DBSession,
) -> AsyncGenerator[ArtifactRepository, None]:
    yield ArtifactRepository(session)


async def get_rm_repo(
    session: DBSession,
) -> AsyncGenerator[RunMetricRepository, None]:
    yield RunMetricRepository(session)


async def get_ci_repo(
    session: DBSession,
) -> AsyncGenerator[ComparisonIndicatorRepository, None]:
    yield ComparisonIndicatorRepository(session)


async def get_dp_job_repo(session: DBSession) -> AsyncGenerator[DPJobRepository, None]:
    yield DPJobRepository(session)


# Typed dependencies
OrgRepo = Annotated[OrgRepository, Depends(get_org_repo)]
ProjectRepo = Annotated[ProjectRepository, Depends(get_project_repo)]
BatchRepo = Annotated[BatchRepository, Depends(get_batch_repo)]
AggregationRepo = Annotated[AggregationRepository, Depends(get_aggregation_repo)]
RunRepo = Annotated[RunRepository, Depends(get_run_repo)]
RunPinRepo = Annotated[RunPinRepository, Depends(get_run_pin_repo)]
ArtifactRepo = Annotated[ArtifactRepository, Depends(get_artifact_repo)]
RMRepo = Annotated[RunMetricRepository, Depends(get_rm_repo)]
CIRepo = Annotated[ComparisonIndicatorRepository, Depends(get_ci_repo)]
DPJobRepo = Annotated[DPJobRepository, Depends(get_dp_job_repo)]


# Path parameter dependencies with validation
async def get_org_or_404(
    org_id: Annotated[str, Path()],
    repo: OrgRepo,
) -> Org:
    """Get org by ID or raise 404"""
    org = await repo.get_by_id(org_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization not found: {org_id}",
        )
    return org


async def get_project_or_404(
    project_id: Annotated[str, Path()],
    repo: ProjectRepo,
) -> Project:
    """Get project by ID or raise 404"""
    project = await repo.get_by_id(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project not found: {project_id}",
        )
    return project


async def get_batch_or_404(
    batch_id: Annotated[str, Path()],
    repo: BatchRepo,
) -> Batch:
    """Get batch by ID or raise 404"""
    batch = await repo.get_by_id(batch_id)
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch not found: {batch_id}",
        )
    return batch


async def get_aggregation_or_404(
    aggregation_id: Annotated[str, Path()],
    repo: AggregationRepo,
) -> Aggregation:
    """Get aggregation by ID or raise 404"""
    aggregation = await repo.get_by_id(aggregation_id)
    if not aggregation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Aggregation not found: {aggregation_id}",
        )
    return aggregation


async def get_run_or_404(
    run_id: Annotated[str, Path()],
    repo: RunRepo,
) -> Run:
    """Get run by ID or raise 404"""
    run = await repo.get_by_id(run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run not found: {run_id}",
        )
    return run


# Typed path dependencies
OrgPath = Annotated[Org, Depends(get_org_or_404)]
ProjectPath = Annotated[Project, Depends(get_project_or_404)]
BatchPath = Annotated[Batch, Depends(get_batch_or_404)]
AggregationPath = Annotated[Aggregation, Depends(get_aggregation_or_404)]
RunPath = Annotated[Run, Depends(get_run_or_404)]
