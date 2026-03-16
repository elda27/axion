"""FastAPI application factory"""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, cast

from axion_lab_server.shared.kernel import close_db, run_startup_migrations
from axion_lab_server.shared.libs.config import Settings, get_settings
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

DEFAULT_UI_DIST_DIR = Path(__file__).resolve().parents[5] / "axion_lab_ui" / "dist"


def _get_api_routers() -> tuple[Any, ...]:
    from axion_lab_server.apps.api.routers import (
        aggregations_router,
        artifacts_router,
        batches_router,
        ci_router,
        dp_router,
        orgs_router,
        pins_router,
        projects_router,
        rm_router,
        runs_router,
    )

    return (
        orgs_router,
        projects_router,
        batches_router,
        aggregations_router,
        runs_router,
        artifacts_router,
        pins_router,
        rm_router,
        ci_router,
        dp_router,
    )


def _include_api_routes(
    app: FastAPI, prefix: str, *, include_in_schema: bool = True
) -> None:
    for router in _get_api_routers():
        app.include_router(router, prefix=prefix, include_in_schema=include_in_schema)


def _resolve_ui_dist_dir(settings: Settings) -> Path | None:
    candidates: list[Path] = []
    if settings.ui_dist_dir:
        candidates.append(Path(settings.ui_dist_dir).expanduser())
    candidates.append(DEFAULT_UI_DIST_DIR)

    for candidate in candidates:
        index_path = candidate / "index.html"
        if index_path.is_file():
            return candidate.resolve()
    return None


def _resolve_ui_file(ui_dist_dir: Path, request_path: str) -> Path | None:
    normalized_path = request_path.strip("/")
    index_path = ui_dist_dir / "index.html"
    if not normalized_path:
        return index_path

    candidate = (ui_dist_dir / normalized_path).resolve()
    try:
        candidate.relative_to(ui_dist_dir)
    except ValueError:
        return None

    if candidate.is_file():
        return candidate

    if Path(normalized_path).suffix:
        return None

    return index_path


def _mount_ui(app: FastAPI, settings: Settings) -> None:
    ui_dist_dir = _resolve_ui_dist_dir(settings)
    if ui_dist_dir is None:
        return

    api_prefixes = (settings.api_prefix, f"/api{settings.api_prefix}")

    @app.get("/{ui_path:path}", include_in_schema=False)
    async def serve_ui(request: Request, ui_path: str) -> FileResponse:
        request_path = request.url.path
        if any(
            request_path == prefix or request_path.startswith(f"{prefix}/")
            for prefix in api_prefixes
        ):
            raise HTTPException(status_code=404)

        ui_file = _resolve_ui_file(ui_dist_dir, ui_path)
        if ui_file is None:
            raise HTTPException(status_code=404)
        return FileResponse(ui_file)


def create_app(*, run_migrations_on_startup: bool = True) -> FastAPI:
    """Create and configure the FastAPI application"""
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        """Application lifespan manager"""
        if run_migrations_on_startup:
            await asyncio.to_thread(run_startup_migrations)
        yield
        await close_db()

    app = FastAPI(
        title="axion-lab",
        description="Artifact-first Experiment Evaluation System",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        middleware_class=cast(Any, CORSMiddleware),
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    prefix = settings.api_prefix
    _include_api_routes(app, prefix)
    _include_api_routes(app, f"/api{prefix}", include_in_schema=False)

    @app.get("/health")
    async def health_check() -> dict:
        """Health check endpoint"""
        return {"status": "healthy", "version": "0.1.0"}

    _mount_ui(app, settings)

    return app


# Create default application instance
app = create_app()
