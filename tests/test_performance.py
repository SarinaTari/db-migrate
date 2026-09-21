from __future__ import annotations

from dbmigrate.performance import measure_call


def test_measure_call_returns_callback_result() -> None:
    result = measure_call(
        "test-operation",
        lambda: 42,
    )

    assert result == 42


def test_measure_call_preserves_exceptions() -> None:
    def fail() -> None:
        raise RuntimeError("failure")

    try:
        measure_call(
            "test-operation",
            fail,
        )
    except RuntimeError as exc:
        assert str(exc) == "failure"
    else:
        raise AssertionError(
            "Expected RuntimeError."
        )