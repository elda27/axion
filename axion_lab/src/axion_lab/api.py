"""Minimal function-based high-level API for run/artifact registration."""

from __future__ import annotations

import os
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

from axion_lab.client import AxionLabClient
from axion_lab.schemas import ArtifactResponse, RunResponse

AXION_LAB_ORG_ENV = "AXION_LAB_ORG"
AXION_LAB_PROJECT_ENV = "AXION_LAB_PROJECT"
AXION_LAB_BATCH_ENV = "AXION_LAB_BATCH"

_active_run_id: str | None = None


# ---------------------------------------------------------------------------
# Series state  — auto-incrementing step counter per (run_id, tag)
# ---------------------------------------------------------------------------

class _SeriesState:
    """Thread-safe, per-(run, tag) step counter for time-series logging."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        # key = (run_id, tag) → next step value
        self._counters: dict[tuple[str, str], int] = {}

    def next_step(self, run_id: str, tag: str) -> int:
        """Return the current step for *(run_id, tag)* and advance by 1."""
        key = (run_id, tag)
        with self._lock:
            step = self._counters.get(key, 0)
            self._counters[key] = step + 1
            return step

    def reset(self, run_id: str | None = None) -> None:
        """Reset counters.

        If *run_id* is given only that run's counters are cleared;
        otherwise **all** counters are dropped.
        """
        with self._lock:
            if run_id is None:
                self._counters.clear()
            else:
                self._counters = {
                    k: v for k, v in self._counters.items() if k[0] != run_id
                }


_series_state = _SeriesState()


@dataclass(frozen=True)
class _ContextNames:
    org: str
    project: str
    batch: str


def create_run(
    run_name: str,
    *,
    org: str | None = None,
    project: str | None = None,
    tags: list[str] | None = None,
    note: str | None = None,
    client: AxionLabClient | None = None,
) -> RunResponse:
    """Create a run using `.env` context and set it as active run.

    Parameters
    ----------
    run_name:
        Human-readable name for the run.
    org:
        Organisation name.  Overrides the ``AXION_LAB_ORG`` env var when
        provided.
    project:
        Project name.  Overrides the ``AXION_LAB_PROJECT`` env var when
        provided.
    tags:
        Optional list of tags to attach to the run.
    note:
        Optional free-text note.
    client:
        An existing :class:`AxionLabClient` instance.  When *None* a
        temporary client is created and closed automatically.
    """
    with _borrow_client(client) as resolved_client:
        context = _load_context_names(org=org, project=project)
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


def append_series(
    *,
    tag: str,
    kind: str,
    type: str,
    payload: Any,
    step: int | None = None,
    wall: float | None = None,
    meta: dict[str, Any] | None = None,
    run_id: str | None = None,
    client: AxionLabClient | None = None,
) -> ArtifactResponse:
    """Append a data-point to a time-series identified by *tag*.

    This is a thin wrapper around :func:`create_artifact` that
    automatically manages an incrementing **step** counter and records
    wall-clock time, similar to TensorBoard's ``SummaryWriter``.

    Every artifact kind is supported — ``inline_number`` for scalar
    metrics, but also ``inline_text``, ``url``, ``inline_json``, etc.

    Parameters
    ----------
    tag:
        Series identifier (used as the artifact ``label``).  The step
        counter is maintained per ``(run_id, tag)`` pair.
    kind:
        Artifact kind (e.g. ``"inline_number"``, ``"inline_text"``).
    type:
        Artifact type (e.g. ``"evaluation"``, ``"note"``).
    payload:
        The value to record — number, string, URL, JSON, …
    step:
        Explicit step index.  When *None* (default) the step is
        auto-incremented starting from 0 for each ``(run_id, tag)``.
    wall:
        Wall-clock timestamp (seconds since epoch).  When *None*
        ``time.time()`` is used.
    meta:
        Extra metadata dict.  ``series_step`` and ``series_wall`` keys
        will be injected automatically (existing values are preserved).
    run_id:
        Target run.  Falls back to the active run set by
        :func:`create_run`.
    client:
        An existing :class:`AxionLabClient`.  When *None* a temporary
        one is created and closed automatically.

    Returns
    -------
    ArtifactResponse
        The created artifact, whose ``meta`` contains ``series_step``
        and ``series_wall`` fields.
    """
    resolved_run_id = run_id or _active_run_id
    if not resolved_run_id:
        raise ValueError(
            "run_id is required when there is no active run. "
            "Call create_run(...) first or pass run_id explicitly."
        )

    if step is None:
        step = _series_state.next_step(resolved_run_id, tag)
    if wall is None:
        wall = time.time()

    merged_meta = dict(meta) if meta else {}
    merged_meta.setdefault("series_step", step)
    merged_meta.setdefault("series_wall", wall)
    merged_meta.setdefault("series_tag", tag)

    return create_artifact(
        kind=kind,
        type=type,
        label=tag,
        payload=payload,
        meta=merged_meta,
        run_id=resolved_run_id,
        client=client,
    )() -> str | None:
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


def _load_context_names(
    *,
    org: str | None = None,
    project: str | None = None,
) -> _ContextNames:
    org = org or os.environ.get(AXION_LAB_ORG_ENV)
    project = project or os.environ.get(AXION_LAB_PROJECT_ENV)
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
