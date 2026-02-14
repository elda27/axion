from datetime import UTC, datetime

from axion_server.shared.libs.utils import generate_id, utc_now


def test_generate_id_returns_string() -> None:
    id_ = generate_id()

    assert isinstance(id_, str)
    assert len(id_) > 0


def test_generate_id_returns_unique_values() -> None:
    ids = {generate_id() for _ in range(100)}

    assert len(ids) == 100


def test_utc_now_returns_utc_datetime() -> None:
    now = utc_now()

    assert isinstance(now, datetime)
    assert now.tzinfo == UTC


def test_utc_now_is_recent() -> None:
    before = datetime.now(UTC)
    now = utc_now()
    after = datetime.now(UTC)

    assert before <= now <= after
