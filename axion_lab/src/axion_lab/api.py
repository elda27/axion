"""Minimal function-based high-level API for run/artifact registration."""

from __future__ import annotations

import os
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

from axion_lab.client import AxionLabClient
from axion_lab.schemas import ArtifactResponse, RunResponse

AXION_LAB_ORG_ENV = "AXION_LAB_ORG"
AXION_LAB_PROJECT_ENV = "AXION_LAB_PROJECT"
AXION_LAB_BATCH_ENV = "AXION_LAB_BATCH"

_active_run_id: str | None = None


@dataclass(frozen=True)
class _ContextNames:
    org: str
    project: str
    batch: str


def create_run(
    run_name: str,
    *,
    tags: list[str] | None = None,
    note: str | None = None,
    client: AxionLabClient | None = None,
) -> RunResponse:
    """Create a run using `.env` context and set it as active run."""
    with _borrow_client(client) as resolved_client:
        context = _load_context_names()
        org_id = _get_or_create_org_id(resolved_client, context.org)
        project_id = _get_or_create_project_id(resolved_client, org_id, context.project)
        batch_id = _get_or_create_batch_id(resolved_client, project_id, context.batch)

        run = resolved_client.runs.create(
            batch_id,
            run_name,
            tags=tags,
            note=note,
        )
        set_active_run(run.run_id)
        return run


def create_artifact(
    *,
    kind: str,
    type: str,
    label: str,
    payload: Any,
    meta: dict[str, Any] | None = None,
    run_id: str | None = None,
    client: AxionLabClient | None = None,
) -> ArtifactResponse:
    """Create an artifact for a run.

    If `run_id` is omitted, the active run set by `create_run` is used.
    """
    resolved_run_id = run_id or _active_run_id
    if not resolved_run_id:
        raise ValueError(
            "run_id is required when there is no active run. "
            "Call create_run(...) first or pass run_id explicitly."
        )

    with _borrow_client(client) as resolved_client:
        return resolved_client.artifacts.create(
            resolved_run_id,
            kind=kind,
            type=type,
            label=label,
            payload=payload,
            meta=meta,
        )


def get_active_run_id() -> str | None:
    """Return the current active run ID."""
    return _active_run_id


def set_active_run(run_id: str | None) -> None:
    """Set active run ID for subsequent `create_artifact` calls."""
    global _active_run_id
    _active_run_id = run_id


@contextmanager
def _borrow_client(client: AxionLabClient | None):
    if client is not None:
        yield client
        return

    created = AxionLabClient()
    try:
        yield created
    finally:
        created.close()


def _load_context_names() -> _ContextNames:
    org = os.environ.get(AXION_LAB_ORG_ENV)
    project = os.environ.get(AXION_LAB_PROJECT_ENV)
    batch = os.environ.get(AXION_LAB_BATCH_ENV)
    missing = [
        env_name
        for env_name, value in (
            (AXION_LAB_ORG_ENV, org),
            (AXION_LAB_PROJECT_ENV, project),
            (AXION_LAB_BATCH_ENV, batch),
        )
        if not value
    ]
    if missing:
        names = ", ".join(missing)
        raise ValueError(f"Missing required environment variables: {names}")

    assert org is not None
    assert project is not None
    assert batch is not None

    return _ContextNames(org=org, project=project, batch=batch)


def _get_or_create_org_id(client: AxionLabClient, org_name: str) -> str:
    cursor: str | None = None
    while True:
        page = client.orgs.list(limit=100, cursor=cursor)
        for item in page.items:
            if item.name == org_name:
                return item.org_id
        if not page.next_cursor:
            break
        cursor = page.next_cursor

    return client.orgs.create(org_name).org_id


def _get_or_create_project_id(
    client: AxionLabClient, org_id: str, project_name: str
) -> str:
    cursor: str | None = None
    while True:
        page = client.projects.list(org_id, limit=100, cursor=cursor)
        for item in page.items:
            if item.name == project_name:
                return item.project_id
        if not page.next_cursor:
            break
        cursor = page.next_cursor

    return client.projects.create(org_id, project_name).project_id


def _get_or_create_batch_id(
    client: AxionLabClient, project_id: str, batch_name: str
) -> str:
    cursor: str | None = None
    while True:
        page = client.batches.list(project_id, limit=100, cursor=cursor)
        for item in page.items:
            if item.name == batch_name:
                return item.batch_id
        if not page.next_cursor:
            break
        cursor = page.next_cursor

    return client.batches.create(project_id, batch_name).batch_id
