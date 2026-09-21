from __future__ import annotations

import logging

import pytest

from dbmigrate.logging_config import (
    LoggingOptions,
    configure_logging,
    get_logger,
)


def test_default_logging_level_is_warning() -> None:
    logger = configure_logging()

    assert logger.level == logging.WARNING


def test_verbose_logging_enables_debug() -> None:
    logger = configure_logging(
        LoggingOptions(verbose=True)
    )

    assert logger.level == logging.DEBUG


def test_quiet_logging_only_reports_errors() -> None:
    logger = configure_logging(
        LoggingOptions(quiet=True)
    )

    assert logger.level == logging.ERROR


def test_custom_log_level() -> None:
    logger = configure_logging(
        LoggingOptions(level="INFO")
    )

    assert logger.level == logging.INFO


def test_invalid_log_level() -> None:
    with pytest.raises(ValueError):
        configure_logging(
            LoggingOptions(level="INVALID")
        )


def test_logger_name() -> None:
    logger = get_logger()

    assert logger.name == "dbmigrate"


def test_named_logger() -> None:
    logger = get_logger("runner")

    assert logger.name == "dbmigrate.runner"