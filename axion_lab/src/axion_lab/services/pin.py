"""Pin service."""

from __future__ import annotations

from axion_lab.schemas import PinCreate, PinResponse, PinType
from axion_lab.services._http import HttpTransport


class PinService:
    """Operations for run pins (champion / user_selected)."""

    def __init__(self, http: HttpTransport) -> None:
        self._http = http

    def create(self, run_id: str, pin_type: PinType | str) -> PinResponse:
        """Pin a run as champion or user_selected."""
        body = PinCreate(pin_type=PinType(pin_type))
        data = self._http.post(
            f"/runs/{run_id}/pins",
            json=body.model_dump(by_alias=True),
        )
        return PinResponse.model_validate(data)

    def delete(self, run_id: str, pin_type: PinType | str) -> None:
        """Remove a pin from a run."""
        self._http.delete(f"/runs/{run_id}/pins/{PinType(pin_type).value}")
