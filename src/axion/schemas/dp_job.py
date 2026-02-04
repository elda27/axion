"""DP Job schemas"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class DPJobStatus(str, Enum):
    """DP Job status enumeration"""

    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


class DPJobMode(str, Enum):
    """DP Job mode enumeration"""

    ACTIVE_ONLY = "active_only"
    INCLUDE_GARBAGE = "include_garbage"


class DPJobCreate(BaseModel):
    """Schema for creating a DP job"""

    mode: DPJobMode = DPJobMode.ACTIVE_ONLY
    recompute: bool = False


class DPJobResponse(BaseModel):
    """Schema for DP job response"""

    job_id: str = Field(..., alias="jobId")
    batch_id: str = Field(..., alias="batchId")
    mode: DPJobMode
    recompute: bool
    status: DPJobStatus
    requested_by: str | None = Field(None, alias="requestedBy")
    created_at: datetime = Field(..., alias="createdAt")
    started_at: datetime | None = Field(None, alias="startedAt")
    finished_at: datetime | None = Field(None, alias="finishedAt")
    error_text: str | None = Field(None, alias="errorText")

    model_config = {"populate_by_name": True, "from_attributes": True}
