from __future__ import annotations

from dbmigrate.ci import (
    CICheckResult,
    CIReport,
)


def test_ci_check_result() -> None:
    result = CICheckResult(
        name="validation",
        passed=True,
        message="Everything is valid.",
    )

    assert result.name == "validation"
    assert result.passed is True


def test_ci_report_passes_when_all_checks_pass() -> None:
    report = CIReport(
        checks=(
            CICheckResult(
                name="one",
                passed=True,
                message="ok",
            ),
            CICheckResult(
                name="two",
                passed=True,
                message="ok",
            ),
        )
    )

    assert report.passed is True
    assert report.passed_count == 2
    assert report.failed_count == 0


def test_ci_report_fails_when_check_fails() -> None:
    report = CIReport(
        checks=(
            CICheckResult(
                name="one",
                passed=True,
                message="ok",
            ),
            CICheckResult(
                name="two",
                passed=False,
                message="failed",
            ),
        )
    )

    assert report.passed is False
    assert report.passed_count == 1
    assert report.failed_count == 1


def test_ci_report_format() -> None:
    report = CIReport(
        checks=(
            CICheckResult(
                name="validation",
                passed=True,
                message="valid",
            ),
        )
    )

    output = report.format()

    assert "dbmigrate CI" in output
    assert "[PASS] validation: valid" in output
    assert "CI checks passed." in output