from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from axion_server.apps.api.routers.comparison_indicators import (
    _build_ci_response,
    list_comparison_indicators_by_batch,
    list_comparison_indicators_by_run,
)


def _ci(
    *,
    ci_id: str = "ci-1",
    run_id: str = "run-1",
    value_json: str = "",
    baseline_ref: str | None = None,
):
    return SimpleNamespace(
        ci_id=ci_id,
        run_id=run_id,
        key="delta_vs_champion_mean",
        value_json=value_json,
        baseline_ref=baseline_ref,
        computed_at=datetime(2026, 2, 12, tzinfo=UTC),
        version=1,
    )


def test_build_ci_response_parses_json_value() -> None:
    ci = _ci(value_json='{"delta": 0.05}')

    response = _build_ci_response(ci)

    assert response.ci_id == "ci-1"
    assert response.run_id == "run-1"
    assert response.value == {"delta": 0.05}


def test_build_ci_response_handles_empty_value() -> None:
    ci = _ci(value_json="")

    response = _build_ci_response(ci)

    assert response.value is None


def test_build_ci_response_handles_scalar_value() -> None:
    ci = _ci(value_json="0.95", baseline_ref="run-champ")

    response = _build_ci_response(ci)

    assert response.value == 0.95
    assert response.baseline_ref == "run-champ"


@pytest.mark.asyncio
async def test_list_comparison_indicators_by_run_returns_items() -> None:
    run = SimpleNamespace(run_id="run-123")
    repo = Mock()
    repo.list_by_run = AsyncMock(
        return_value=[
            _ci(ci_id="ci-1", run_id="run-123", value_json='{"x":1}'),
            _ci(ci_id="ci-2", run_id="run-123", value_json="0.5"),
        ]
    )

    result = await list_comparison_indicators_by_run(run=run, repo=repo)

    repo.list_by_run.assert_awaited_once_with("run-123")
    assert [item.ci_id for item in result] == ["ci-1", "ci-2"]
    assert result[0].value == {"x": 1}
    assert result[1].value == 0.5


@pytest.mark.asyncio
async def test_list_comparison_indicators_by_batch_returns_cursor_page() -> None:
    batch = SimpleNamespace(batch_id="batch-123")
    repo = Mock()
    repo.list_by_batch = AsyncMock(
        return_value=(
            [
                _ci(ci_id="ci-a", run_id="run-a", value_json='{"a":1}'),
                _ci(ci_id="ci-b", run_id="run-b", value_json='{"b":2}'),
            ],
            "next-cur",
        )
    )

    page = await list_comparison_indicators_by_batch(
        batch=batch,
        repo=repo,
        key="delta_vs_champion_mean",
        limit=2,
        cursor="cur-1",
    )

    repo.list_by_batch.assert_awaited_once_with(
        "batch-123", key="delta_vs_champion_mean", limit=2, cursor="cur-1"
    )
    assert page.has_more is True
    assert page.next_cursor == "next-cur"
    assert [item.ci_id for item in page.items] == ["ci-a", "ci-b"]


@pytest.mark.asyncio
async def test_list_comparison_indicators_by_batch_has_more_false() -> None:
    batch = SimpleNamespace(batch_id="batch-xyz")
    repo = Mock()
    repo.list_by_batch = AsyncMock(return_value=([_ci(ci_id="ci-z")], None))

    page = await list_comparison_indicators_by_batch(batch=batch, repo=repo)

    assert page.has_more is False
    assert page.next_cursor is None
    assert len(page.items) == 1
