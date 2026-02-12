"""Project schemas"""

from datetime import datetime

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    """Schema for creating a project"""

    name: str = Field(..., min_length=1, max_length=255)


class ProjectResponse(BaseModel):
    """Schema for project response"""

    project_id: str = Field(..., alias="projectId")
    org_id: str = Field(..., alias="orgId")
    name: str
    created_at: datetime = Field(..., alias="createdAt")

    model_config = {"populate_by_name": True, "from_attributes": True}
