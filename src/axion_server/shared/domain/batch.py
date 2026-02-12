"""Batch schemas"""

from datetime import datetime

from pydantic import BaseModel, Field


class BatchCreate(BaseModel):
    """Schema for creating a batch"""

    name: str = Field(..., min_length=1, max_length=255)


class BatchResponse(BaseModel):
    """Schema for batch response"""

    batch_id: str = Field(..., alias="batchId")
    project_id: str = Field(..., alias="projectId")
    name: str
    created_at: datetime = Field(..., alias="createdAt")

    model_config = {"populate_by_name": True, "from_attributes": True}
