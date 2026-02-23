"""Axion Lab SDK service layer.

Each service class encapsulates HTTP interactions for a single
domain entity (Org, Project, Batch, …).  The :class:`AxionLabClient`
facade (:pymod:`axion_lab.client`) exposes service instances as properties.
"""

from axion_lab.services._http import AxionLabHTTPError, HttpTransport
from axion_lab.services.aggregation import AggregationService
from axion_lab.services.artifact import ArtifactService
from axion_lab.services.batch import BatchService
from axion_lab.services.comparison_indicator import ComparisonIndicatorService
from axion_lab.services.dp import DPService
from axion_lab.services.org import OrgService
from axion_lab.services.pin import PinService
from axion_lab.services.project import ProjectService
from axion_lab.services.quality_metric import QualityMetricService
from axion_lab.services.run import RunService

__all__ = [
    "AxionLabHTTPError",
    "HttpTransport",
    "OrgService",
    "ProjectService",
    "BatchService",
    "AggregationService",
    "RunService",
    "ArtifactService",
    "PinService",
    "QualityMetricService",
    "ComparisonIndicatorService",
    "DPService",
]
