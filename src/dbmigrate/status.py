"""Migration status inspection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .history import MigrationRecord
from .migration import Migration
from .runner import MigrationRunner, MigrationRunnerError


class MigrationStatusError(Exception):
    """Raised when migration status cannot be determined."""


@dataclass(frozen=True)
class MigrationStatus:
    """Describe the current migration state."""

    total_count: int
    applied_count: int
    pending_count: int
    missing_count: int
    current: Migration | None
    pending: list[Migration]
    missing: list[MigrationRecord]

    @property
    def is_up_to_date(self) -> bool:
        """Return whether all known migrations are applied."""
        return (
            self.pending_count == 0
            and self.missing_count == 0
        )


class MigrationStatusInspector:
    """Inspect migration state using migration history."""

    def __init__(
        self,
        runner: MigrationRunner,
    ) -> None:
        self.runner = runner

    def inspect(
        self,
        migrations: Sequence[Migration],
    ) -> MigrationStatus:
        """Inspect applied, pending, and missing migrations."""
        try:
            applied = self.runner.applied(
                migrations
            )
            pending = self.runner.pending(
                migrations
            )
            history = self.runner.history.list_applied()
        except Exception as exc:
            raise MigrationStatusError(
                f"Could not inspect migration status: {exc}"
            ) from exc

        migration_versions = {
            migration.version
            for migration in migrations
        }

        missing = [
            record
            for record in history
            if record.version not in migration_versions
        ]

        current = applied[-1] if applied else None

        return MigrationStatus(
            total_count=len(migrations),
            applied_count=len(applied),
            pending_count=len(pending),
            missing_count=len(missing),
            current=current,
            pending=list(pending),
            missing=missing,
        )