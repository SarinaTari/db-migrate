"""Performance measurement utilities for dbmigrate."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import time
from typing import Iterator

from .logging_config import get_logger


@dataclass(frozen=True)
class PerformanceMeasurement:
    """Describe one measured operation."""

    operation: str
    elapsed_seconds: float

    @property
    def elapsed_milliseconds(self) -> float:
        """Return elapsed time in milliseconds."""
        return self.elapsed_seconds * 1000.0


@contextmanager
def measure(
    operation: str,
    *,
    log: bool = True,
) -> Iterator[None]:
    """Measure the execution time of an operation."""
    start = time.perf_counter()

    try:
        yield
    finally:
        elapsed = time.perf_counter() - start

        if log:
            get_logger().debug(
                "%s completed in %.3f ms",
                operation,
                elapsed * 1000.0,
            )


def measure_call(
    operation: str,
    callback,
):
    """Measure and execute a callable."""
    start = time.perf_counter()

    try:
        return callback()
    finally:
        elapsed = time.perf_counter() - start

        get_logger().debug(
            "%s completed in %.3f ms",
            operation,
            elapsed * 1000.0,
        )