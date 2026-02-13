"""Artifact schemas"""

import json
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class ArtifactKind(StrEnum):
    """Artifact kind enumeration"""

    URL = "url"
    LOCAL = "local"
    INLINE_TEXT = "inline_text"
    INLINE_NUMBER = "inline_number"
    INLINE_JSON = "inline_json"


class ArtifactType(StrEnum):
    """Artifact type enumeration"""

    LANGFUSE_TRACE = "langfuse_trace"
    OBJECT_STORAGE = "object_storage"
    NOTE = "note"
    DASHBOARD = "dashboard"
    GIT_COMMIT = "git_commit"
    FILE = "file"
    EVALUATION = "evaluation"
    LATENCY_P95_MS = "latency_p95_ms"
    COST_USD = "cost_usd"
    OTHER = "other"


class ArtifactCreate(BaseModel):
    """Schema for creating an artifact"""

    kind: ArtifactKind
    type: str = Field(..., min_length=1, max_length=50)
    label: str = Field(..., min_length=1, max_length=255)
    payload: Any  # URL/path string, number, or JSON object
    meta: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_payload_for_kind(self) -> "ArtifactCreate":
        """Validate payload matches kind"""
        if self.kind in (
            ArtifactKind.URL,
            ArtifactKind.LOCAL,
            ArtifactKind.INLINE_TEXT,
        ):
            if not isinstance(self.payload, str):
                raise ValueError(f"payload must be string for kind={self.kind}")
        elif self.kind == ArtifactKind.INLINE_NUMBER:
            if not isinstance(self.payload, int | float):
                raise ValueError(f"payload must be number for kind={self.kind}")
        # INLINE_JSON can be any JSON-serializable value
        return self


class ArtifactResponse(BaseModel):
    """Schema for artifact response"""

    artifact_id: str = Field(..., alias="artifactId")
    run_id: str = Field(..., alias="runId")
    kind: ArtifactKind
    type: str
    label: str
    payload: Any
    meta: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(..., alias="createdAt")

    model_config = {"populate_by_name": True, "from_attributes": True}

    @field_validator("meta", mode="before")
    @classmethod
    def parse_meta(cls, v: Any) -> dict[str, Any]:
        """Parse meta from JSON string if needed"""
        if isinstance(v, str):
            return json.loads(v)
        return v
