"""API routers package"""

from axion_lab_server.apps.api.routers.aggregations import router as aggregations_router
from axion_lab_server.apps.api.routers.artifacts import router as artifacts_router
from axion_lab_server.apps.api.routers.batches import router as batches_router
from axion_lab_server.apps.api.routers.comparison_indicators import router as ci_router
from axion_lab_server.apps.api.routers.dp import router as dp_router
from axion_lab_server.apps.api.routers.orgs import router as orgs_router
from axion_lab_server.apps.api.routers.pins import router as pins_router
from axion_lab_server.apps.api.routers.projects import router as projects_router
from axion_lab_server.apps.api.routers.run_metrics import router as rm_router
from axion_lab_server.apps.api.routers.runs import router as runs_router

__all__ = [
    "orgs_router",
    "projects_router",
    "batches_router",
    "aggregations_router",
    "runs_router",
    "artifacts_router",
    "pins_router",
    "rm_router",
    "ci_router",
    "dp_router",
]
