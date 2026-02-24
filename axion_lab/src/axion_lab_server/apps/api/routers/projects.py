"""Project API router"""

from fastapi import APIRouter, HTTPException, status

from axion_lab_server.apps.api.deps import OrgPath, ProjectPath, ProjectRepo
from axion_lab_server.shared.domain import (
    CursorPaginatedResponse,
    ProjectCreate,
    ProjectResponse,
)

router = APIRouter(tags=["Projects"])


@router.post(
    "/orgs/{org_id}/projects",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_project(
    data: ProjectCreate,
    org: OrgPath,
    repo: ProjectRepo,
) -> ProjectResponse:
    """Create a new project in an organization"""
    existing = await repo.get_by_name(org.org_id, data.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Project with name '{data.name}' already exists in this organization",
        )
    project = await repo.create(org.org_id, data)
    return ProjectResponse.model_validate(project)


@router.get(
    "/orgs/{org_id}/projects",
    response_model=CursorPaginatedResponse[ProjectResponse],
)
async def list_projects(
    org: OrgPath,
    repo: ProjectRepo,
    limit: int = 20,
    cursor: str | None = None,
) -> CursorPaginatedResponse[ProjectResponse]:
    """List projects in an organization"""
    projects, next_cursor = await repo.list_by_org(
        org.org_id, limit=limit, cursor=cursor
    )
    return CursorPaginatedResponse(
        items=[ProjectResponse.model_validate(p) for p in projects],
        next_cursor=next_cursor,
        has_more=next_cursor is not None,
    )


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(project: ProjectPath) -> ProjectResponse:
    """Get project by ID"""
    return ProjectResponse.model_validate(project)
