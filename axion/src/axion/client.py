"""Axion SDK client — facade over domain-specific services.

Usage::

    from axion import AxionClient

    client = AxionClient()                       # http://localhost:8000
    client = AxionClient("http://api.example.com")

    org = client.orgs.create("My Org")
    project = client.projects.create(org.org_id, "Eval Project")
    batch = client.batches.create(project.project_id, "Batch-1")
    run = client.runs.create(batch.batch_id, "run-v1", tags=["gpt-4o"])
    artifact = client.artifacts.create(
        run.run_id, kind="inline_number", type="evaluation",
        label="score", payload=0.95,
    )
"""

from __future__ import annotations

import os

import httpx

from axion.services._http import HttpTransport
from axion.services.artifact import ArtifactService
from axion.services.batch import BatchService
from axion.services.comparison_indicator import ComparisonIndicatorService
from axion.services.dp import DPService
from axion.services.org import OrgService
from axion.services.pin import PinService
from axion.services.project import ProjectService
from axion.services.quality_metric import QualityMetricService
from axion.services.run import RunService

_DEFAULT_BASE_URL = "http://localhost:8000"


class AxionClient:
    """High-level Axion SDK client.

    Acts as a **facade**: all domain logic lives in service classes
    exposed as read-only properties (``orgs``, ``projects``, …).

    Parameters
    ----------
    base_url:
        Axion API root (without ``/v1``).  Falls back to the
        ``AXION_BASE_URL`` environment variable, then to
        ``http://localhost:8000``.
    api_prefix:
        API version prefix.  Default ``/v1``.
    timeout:
        Request timeout in seconds.
    """

    def __init__(
        self,
        base_url: str | None = None,
        *,
        api_prefix: str = "/v1",
        timeout: float = 30.0,
    ) -> None:
        resolved_url = base_url or os.environ.get("AXION_BASE_URL", _DEFAULT_BASE_URL)
        self._base_url = resolved_url.rstrip("/")
        self._api_url = f"{self._base_url}{api_prefix}"

        self._httpx = httpx.Client(base_url=self._api_url, timeout=timeout)
        self._http = HttpTransport(self._httpx)

        # ── service instances (lazy-free: lightweight classes) ──
        self._orgs = OrgService(self._http)
        self._projects = ProjectService(self._http)
        self._batches = BatchService(self._http)
        self._runs = RunService(self._http)
        self._artifacts = ArtifactService(self._http)
        self._pins = PinService(self._http)
        self._quality_metrics = QualityMetricService(self._http)
        self._comparison_indicators = ComparisonIndicatorService(self._http)
        self._dp = DPService(self._http)

    # ── service properties ────────────────────────────────────

    @property
    def orgs(self) -> OrgService:
        """Organization operations."""
        return self._orgs

    @property
    def projects(self) -> ProjectService:
        """Project operations."""
        return self._projects

    @property
    def batches(self) -> BatchService:
        """Batch operations."""
        return self._batches

    @property
    def runs(self) -> RunService:
        """Run operations."""
        return self._runs

    @property
    def artifacts(self) -> ArtifactService:
        """Artifact operations."""
        return self._artifacts

    @property
    def pins(self) -> PinService:
        """Pin operations."""
        return self._pins

    @property
    def quality_metrics(self) -> QualityMetricService:
        """Quality metric operations (read-only, computed via DP)."""
        return self._quality_metrics

    @property
    def comparison_indicators(self) -> ComparisonIndicatorService:
        """Comparison indicator operations (read-only, computed via DP)."""
        return self._comparison_indicators

    @property
    def dp(self) -> DPService:
        """DP (differential processing) job operations."""
        return self._dp

    # ── top-level helpers ─────────────────────────────────────

    def health_check(self) -> dict[str, object]:
        """Call ``GET /health`` (outside the versioned prefix)."""
        resp = self._httpx.get(f"{self._base_url}/health")
        resp.raise_for_status()
        return resp.json()

    # ── context-manager / lifecycle ───────────────────────────

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._httpx.close()

    def __enter__(self) -> AxionClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def __repr__(self) -> str:
        return f"AxionClient(base_url={self._base_url!r})"
