"""Centralized logging configuration for dbmigrate."""

from __future__ import annotations

import logging
from dataclasses import dataclass


LOGGER_NAME = "dbmigrate"


@dataclass(frozen=True)
class LoggingOptions:
    """Configure diagnostic logging."""

    level: str = "WARNING"
    quiet: bool = False
    verbose: bool = False


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a dbmigrate logger."""
    if name is None:
        return logging.getLogger(LOGGER_NAME)

    return logging.getLogger(f"{LOGGER_NAME}.{name}")


def configure_logging(
    options: LoggingOptions | str | None = None,
) -> None:
    """Configure centralized CLI logging.

    ``options`` may be either a ``LoggingOptions`` instance or a
    logging-level string for backwards compatibility with the CLI.
    """
    if options is None:
        options = LoggingOptions()

    if isinstance(options, str):
        options = LoggingOptions(level=options)

    level_name = options.level.upper()

    if options.quiet:
        level_name = "ERROR"
    elif options.verbose:
        level_name = "DEBUG"

    level = getattr(logging, level_name, None)

    if not isinstance(level, int):
        raise ValueError(
            f"Unknown logging level: {options.level}"
        )

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(level)

    handler = None

    for existing_handler in logger.handlers:
        if getattr(
            existing_handler,
            "_dbmigrate_handler",
            False,
        ):
            handler = existing_handler
            break

    if handler is None:
        handler = logging.StreamHandler()
        handler._dbmigrate_handler = True  # type: ignore[attr-defined]

        handler.setFormatter(
            logging.Formatter(
                "%(levelname)s: %(message)s"
            )
        )

        logger.addHandler(handler)

    handler.setLevel(level)

    logger.propagate = False

    return logger