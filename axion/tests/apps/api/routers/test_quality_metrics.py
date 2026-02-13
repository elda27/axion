from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from axion_server.apps.api.routers.quality_metrics import (
    _build_qm_response,
    list_quality_metrics_by_batch,
    list_quality_metrics_by_run,
)
from axion_server.shared.domain import QualityMetricSource


def _metric(*, qm_id: str = "qm-1", run_id: str = "run-1", value_json: str = ""):
    return SimpleNamespace(
        qm_id=qm_id,
        run_id=run_id,
        key="accuracy",
        value_json=value_json,
        source=QualityMetricSource.DERIVED,
        computed_at=datetime(2026, 2, 12, tzinfo=UTC),
        version=1,
    )


def test_build_qm_response_parses_json_value() -> None:
    qm = _metric(value_json='{"score": 0.98}')

    response = _build_qm_response(qm)

    assert response.qm_id == "qm-1"
    assert response.run_id == "run-1"
    assert response.value == {"score": 0.98}


def test_build_qm_response_handles_empty_value() -> None:
    qm = _metric(value_json="")

    response = _build_qm_response(qm)

    assert response.value is None


@pytest.mark.asyncio
async def test_list_quality_metrics_by_run_returns_items() -> None:
    run = SimpleNamespace(run_id="run-123")
    repo = Mock()
    repo.list_by_run = AsyncMock(
        return_value=[
            _metric(qm_id="qm-1", run_id="run-123", value_json='{"x":1}'),
            _metric(qm_id="qm-2", run_id="run-123", value_json="10"),
        ]
    )

    result = await list_quality_metrics_by_run(run=run, repo=repo)

    repo.list_by_run.assert_awaited_once_with("run-123")
    assert [item.qm_id for item in result] == ["qm-1", "qm-2"]
    assert result[0].value == {"x": 1}
    assert result[1].value == 10


@pytest.mark.asyncio
async def test_list_quality_metrics_by_batch_returns_cursor_page() -> None:
    batch = SimpleNamespace(batch_id="batch-123")
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

    page = await list_quality_metrics_by_batch(
        batch=batch,
        repo=repo,
        key="accuracy",
        limit=2,
        cursor="cur-1",
    )

    repo.list_by_batch.assert_awaited_once_with(
        "batch-123", key="accuracy", limit=2, cursor="cur-1"
    )
    assert page.has_more is True
    assert page.next_cursor == "next-cur"
    assert [item.qm_id for item in page.items] == ["qm-a", "qm-b"]


@pytest.mark.asyncio
async def test_list_quality_metrics_by_batch_has_more_false_without_cursor() -> None:
    batch = SimpleNamespace(batch_id="batch-xyz")
    repo = Mock()
    repo.list_by_batch = AsyncMock(return_value=([_metric(qm_id="qm-z")], None))

    page = await list_quality_metrics_by_batch(batch=batch, repo=repo)

    assert page.has_more is False
    assert page.next_cursor is None
    assert len(page.items) == 1
