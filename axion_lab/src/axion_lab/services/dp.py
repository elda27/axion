"""DP (Differential Processing) service."""

from __future__ import annotations

from axion_lab.schemas import DPJobCreate, DPJobMode, DPJobResponse
from axion_lab.services._http import HttpTransport


class DPService:
    """Operations for DP computation jobs."""

    def __init__(self, http: HttpTransport) -> None:
        self._http = http

    def trigger(
        self,
        batch_id: str,
        *,
        mode: DPJobMode | str = DPJobMode.ACTIVE_ONLY,
        recompute: bool = False,
    ) -> DPJobResponse:
        """Trigger a DP computation job for a batch."""
        body = DPJobCreate(mode=DPJobMode(mode), recompute=recompute)
        data = self._http.post(
            f"/batches/{batch_id}/dp/compute",
            json=body.model_dump(),
        )
        return DPJobResponse.model_validate(data)

    def get_job(self, job_id: str) -> DPJobResponse:
        """Get the status of a DP job."""
        data = self._http.get(f"/dp/jobs/{job_id}")
        return DPJobResponse.model_validate(data)
