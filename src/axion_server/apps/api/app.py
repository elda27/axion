"""FastAPI application factory"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from axion_server.shared.kernel import close_db
from axion_server.shared.libs.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan manager"""
    # Startup - migrations should be run via `axion db-upgrade` before starting
    yield
    # Shutdown
    await close_db()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    settings = get_settings()

    app = FastAPI(
        title="Axion",
        description="Artifact-first Experiment Evaluation System",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    from axion_server.apps.api.routers import (
        artifacts_router,
        batches_router,
        ci_router,
        dp_router,
        orgs_router,
        pins_router,
        projects_router,
        qm_router,
        runs_router,
    )

    prefix = settings.api_prefix
    app.include_router(orgs_router, prefix=prefix)
    app.include_router(projects_router, prefix=prefix)
    app.include_router(batches_router, prefix=prefix)
    app.include_router(runs_router, prefix=prefix)
    app.include_router(artifacts_router, prefix=prefix)
    app.include_router(pins_router, prefix=prefix)
    app.include_router(qm_router, prefix=prefix)
    app.include_router(ci_router, prefix=prefix)
    app.include_router(dp_router, prefix=prefix)

    @app.get("/health")
    async def health_check() -> dict:
        """Health check endpoint"""
        return {"status": "healthy", "version": "0.1.0"}

    return app


# Create default application instance
app = create_app()
