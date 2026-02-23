"""Project service."""

from __future__ import annotations

from axion_lab.schemas import CursorPaginatedResponse, ProjectCreate, ProjectResponse
from axion_lab.services._http import HttpTransport


class ProjectService:
    """CRUD operations for projects."""

    def __init__(self, http: HttpTransport) -> None:
        self._http = http

    def create(self, org_id: str, name: str) -> ProjectResponse:
        """Create a new project under an organization."""
        data = self._http.post(
            f"/orgs/{org_id}/projects",
            json=ProjectCreate(name=name).model_dump(),
        )
        return ProjectResponse.model_validate(data)

    def list(
        self,
        org_id: str,
        *,
        limit: int = 20,
        cursor: str | None = None,
    ) -> CursorPaginatedResponse[ProjectResponse]:
        """List projects in an organization."""
        params: dict[str, object] = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        data = self._http.get(f"/orgs/{org_id}/projects", params=params)
        return CursorPaginatedResponse[ProjectResponse].model_validate(data)

    def get(self, project_id: str) -> ProjectResponse:
        """Get a project by ID."""
        data = self._http.get(f"/projects/{project_id}")
        return ProjectResponse.model_validate(data)
