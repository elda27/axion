"""Run pin schemas"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class PinType(str, Enum):
    """Pin type enumeration"""

    CHAMPION = "champion"
    USER_SELECTED = "user_selected"


class PinCreate(BaseModel):
    """Schema for creating a pin"""

    pin_type: PinType = Field(..., alias="pinType")

    model_config = {"populate_by_name": True}


class PinResponse(BaseModel):
    """Schema for pin response"""

    pin_id: str = Field(..., alias="pinId")
    run_id: str = Field(..., alias="runId")
    batch_id: str = Field(..., alias="batchId")
    pin_type: PinType = Field(..., alias="pinType")
    pinned_by: str | None = Field(None, alias="pinnedBy")
    pinned_at: datetime = Field(..., alias="pinnedAt")

    model_config = {"populate_by_name": True, "from_attributes": True}
