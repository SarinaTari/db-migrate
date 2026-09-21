"""Migration reproducibility checking."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tempfile
from typing import Sequence

from .database import DatabaseError, SQLiteDatabase
from .migration import Migration
from .runner import MigrationRunner, MigrationRunnerError
from .schema import (
    DatabaseSchema,
    inspect_schema,
)
from .schema_diff import (
    SchemaDiff,
    diff_schemas,
)


class ReproducibilityError(Exception):
    """Raised when reproducibility checking fails."""


@dataclass(frozen=True)
class ReproducibilityReport:
    """Describe whether migrations reproduce a target schema."""

    expected: DatabaseSchema
    actual: DatabaseSchema
    diff: SchemaDiff

    @property
    def is_reproducible(self) -> bool:
        """Return whether the migration set reproduces the schema."""
        return self.diff.is_empty

    @property
    def expected_fingerprint(self) -> str:
        """Return the expected schema fingerprint."""
        return self.expected.fingerprint()

    @property
    def actual_fingerprint(self) -> str:
        """Return the reproduced schema fingerprint."""
        return self.actual.fingerprint()


def _create_temporary_database(
    temporary_directory: str | Path,
) -> SQLiteDatabase:
    """Create a temporary SQLite database in the supplied directory."""
    path = (
        Path(temporary_directory)
        / "reproducibility.db"
    )

    return SQLiteDatabase(path)


def reproduce_schema(
    migrations: Sequence[Migration],
) -> DatabaseSchema:
    """Apply all migrations to a fresh SQLite database."""
    with tempfile.TemporaryDirectory() as temporary_directory:
        database = _create_temporary_database(
            temporary_directory
        )

        try:
            database.connect()

            runner = MigrationRunner(
                database
            )

            runner.apply_all(
                migrations
            )

            return inspect_schema(
                database
            )

        except (
            DatabaseError,
            MigrationRunnerError,
        ) as exc:
            raise ReproducibilityError(
                f"Could not reproduce schema from migrations: {exc}"
            ) from exc

        finally:
            database.close()


def check_reproducibility(
    migrations: Sequence[Migration],
    target_schema: DatabaseSchema,
) -> ReproducibilityReport:
    """Check whether migrations reproduce a target schema."""
    actual_schema = reproduce_schema(
        migrations
    )

    diff = diff_schemas(
        target_schema,
        actual_schema,
    )

    return ReproducibilityReport(
        expected=target_schema,
        actual=actual_schema,
        diff=diff,
    )