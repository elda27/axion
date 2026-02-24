from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock, Mock

import pytest
from axion_lab_server.apps.api.routers.run_metrics import (
    _build_rm_response,
    list_run_metrics_by_batch,
    list_run_metrics_by_run,
)
from axion_lab_server.shared.domain import RunMetricSource
from sqlalchemy.ext.asyncio import AsyncSession


def _metric(*, qm_id: str = "qm-1", run_id: str = "run-1", value_json: str = ""):
    return SimpleNamespace(
        qm_id=qm_id,
        run_id=run_id,
        key="accuracy",
        value_json=value_json,
        source=RunMetricSource.DERIVED,
        computed_at=datetime(2026, 2, 12, tzinfo=UTC),
        version=1,
    )


def test_build_rm_response_parses_json_value() -> None:
    rm = _metric(value_json='{"score": 0.98}')

    response = _build_rm_response(rm, evaluation_types=["evaluation"])

    assert response.qm_id == "qm-1"
    assert response.run_id == "run-1"
    assert response.value == {"score": 0.98}
    assert response.evaluation_types == ["evaluation"]


def test_build_rm_response_handles_empty_value() -> None:
    rm = _metric(value_json="")

    response = _build_rm_response(rm)

    assert response.value is None
    assert response.evaluation_types == []


@pytest.mark.asyncio
async def test_list_run_metrics_by_run_returns_items() -> None:
    run = cast(Any, SimpleNamespace(run_id="run-123"))
    repo = Mock()
    repo.list_by_run = AsyncMock(
        return_value=[
            _metric(qm_id="qm-1", run_id="run-123", value_json='{"x":1}'),
            _metric(qm_id="qm-2", run_id="run-123", value_json="10"),
        ]
    )
    artifact_repo = Mock()
    artifact_repo.session = AsyncMock()

    # Mock _get_evaluation_types_by_run at module level
    import axion_lab_server.apps.api.routers.run_metrics as rm_module

    original = rm_module._get_evaluation_types_by_run

    async def mock_get_eval_types(
        session: AsyncSession, run_ids: list[str]
    ) -> dict[str, list[str]]:
        return {rid: ["evaluation"] for rid in run_ids}

    setattr(rm_module, "_get_evaluation_types_by_run", mock_get_eval_types)
    try:
        result = await list_run_metrics_by_run(
            run=run, repo=repo, artifact_repo=artifact_repo
        )
    finally:
        setattr(rm_module, "_get_evaluation_types_by_run", original)

    repo.list_by_run.assert_awaited_once_with("run-123")
    assert [item.qm_id for item in result] == ["qm-1", "qm-2"]
    assert result[0].value == {"x": 1}
    assert result[0].evaluation_types == ["evaluation"]
    assert result[1].value == 10


@pytest.mark.asyncio
async def test_list_run_metrics_by_batch_returns_cursor_page() -> None:
    batch = cast(Any, SimpleNamespace(batch_id="batch-123"))
    repo = Mock()
    repo.list_by_batch = AsyncMock(
        return_value=(
            [
                _metric(qm_id="qm-a", run_id="run-a", value_json='{"a":1}'),
                _metric(qm_id="qm-b", run_id="run-b", value_json='{"b":2}'),
            ],
            "next-cur",
        )
    )
    artifact_repo = Mock()
    artifact_repo.session = AsyncMock()

    import axion_lab_server.apps.api.routers.run_metrics as rm_module

    original = rm_module._get_evaluation_types_by_run

    async def mock_get_eval_types(
        session: AsyncSession, run_ids: list[str]
    ) -> dict[str, list[str]]:
        return {"run-a": ["evaluation"], "run-b": ["score"]}

    setattr(rm_module, "_get_evaluation_types_by_run", mock_get_eval_types)
    try:
        page = await list_run_metrics_by_batch(
            batch=batch,
            repo=repo,
            artifact_repo=artifact_repo,
            key="accuracy",
            limit=2,
            cursor="cur-1",
        )
    finally:
        setattr(rm_module, "_get_evaluation_types_by_run", original)

    repo.list_by_batch.assert_awaited_once_with(
        "batch-123", key="accuracy", limit=2, cursor="cur-1"
    )
    assert page.has_more is True
    assert page.next_cursor == "next-cur"
    assert [item.qm_id for item in page.items] == ["qm-a", "qm-b"]
    assert page.items[0].evaluation_types == ["evaluation"]
    assert page.items[1].evaluation_types == ["score"]


@pytest.mark.asyncio
async def test_list_run_metrics_by_batch_has_more_false_without_cursor() -> None:
    batch = cast(Any, SimpleNamespace(batch_id="batch-xyz"))
    repo = Mock()
    repo.list_by_batch = AsyncMock(return_value=([_metric(qm_id="qm-z")], None))
    artifact_repo = Mock()
    artifact_repo.session = AsyncMock()

    import axion_lab_server.apps.api.routers.run_metrics as rm_module

    original = rm_module._get_evaluation_types_by_run

    async def mock_get_eval_types(
        session: AsyncSession, run_ids: list[str]
    ) -> dict[str, list[str]]:
        return {}

    setattr(rm_module, "_get_evaluation_types_by_run", mock_get_eval_types)
    try:
        page = await list_run_metrics_by_batch(
            batch=batch, repo=repo, artifact_repo=artifact_repo
        )
    finally:
        setattr(rm_module, "_get_evaluation_types_by_run", original)

    assert page.has_more is False
    assert page.next_cursor is None
    assert len(page.items) == 1
    assert page.items[0].evaluation_types == []
