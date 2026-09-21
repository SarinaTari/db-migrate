"""Migration planning without executing database changes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .history import MigrationHistory
from .migration import Migration


class MigrationPlanningError(Exception):
    """Raised when a migration plan cannot be created."""


@dataclass(frozen=True)
class MigrationPlan:
    """Describe the migrations that would be applied."""

    pending: tuple[Migration, ...]

    @property
    def count(self) -> int:
        """Return the number of pending migrations."""
        return len(self.pending)

    @property
    def is_empty(self) -> bool:
        """Return whether the plan contains no migrations."""
        return not self.pending

    @property
    def versions(self) -> tuple[int, ...]:
        """Return pending migration versions."""
        return tuple(
            migration.version
            for migration in self.pending
        )


class MigrationPlanner:
    """Build migration plans without executing migrations."""

    def __init__(
        self,
        history: MigrationHistory,
    ) -> None:
        """Initialize the migration planner."""
        self.history = history

    def plan(
        self,
        migrations: Sequence[Migration],
    ) -> MigrationPlan:
        """Return the migrations that are currently pending."""
        try:
            self.history.initialize()

            applied_versions = {
                record.version
                for record in self.history.list_applied()
            }

        except Exception as exc:
            raise MigrationPlanningError(
                f"Could not inspect migration history: {exc}"
            ) from exc

        ordered_migrations = sorted(
            migrations,
            key=lambda migration: migration.version,
        )

        pending = tuple(
            migration
            for migration in ordered_migrations
            if migration.version not in applied_versions
        )

        return MigrationPlan(
            pending=pending,
        )