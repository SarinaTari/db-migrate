"""Migration file creation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .migration import (
    MigrationDiscoveryError,
    MigrationParseError,
    discover_migrations,
)


MIGRATION_NAME_PATTERN = re.compile(
    r"^[a-z0-9][a-z0-9_-]*$"
)


class MigrationCreationError(Exception):
    """Raised when a migration cannot be created."""


@dataclass(frozen=True)
class CreatedMigration:
    """Information about a newly created migration."""

    version: int
    name: str
    path: Path

    @property
    def identifier(self) -> str:
        """Return the migration identifier."""
        return f"{self.version:03d}_{self.name}"


def validate_migration_name(name: str) -> str:
    """Validate and return a migration name."""
    if not isinstance(name, str):
        raise MigrationCreationError(
            "Migration name must be a string."
        )

    name = name.strip()

    if not name:
        raise MigrationCreationError(
            "Migration name must not be empty."
        )

    if not MIGRATION_NAME_PATTERN.fullmatch(name):
        raise MigrationCreationError(
            f"Invalid migration name '{name}'. "
            "Use lowercase letters, numbers, underscores, "
            "and hyphens, starting with a lowercase letter "
            "or number."
        )

    return name


def _load_existing_migrations(
    migrations_path: Path,
):
    """Load existing migrations for creation checks."""
    try:
        return discover_migrations(
            migrations_path
        )
    except (
        MigrationDiscoveryError,
        MigrationParseError,
    ) as exc:
        raise MigrationCreationError(
            f"Could not inspect existing migrations: {exc}"
        ) from exc


def _next_version(
    migrations,
) -> int:
    """Return the next available migration version."""
    if not migrations:
        return 1

    return (
        max(
            migration.version
            for migration in migrations
        )
        + 1
    )


def _render_migration(
    version: int,
    name: str,
) -> str:
    """Render a new migration file."""
    return (
        f"-- migration: {version:03d}\n"
        f"-- name: {name}\n"
        "\n"
        "-- +up\n"
        "\n"
        "-- Write your SQL here.\n"
        "\n"
        "-- +down\n"
        "\n"
        "-- Write your rollback SQL here.\n"
    )


def create_migration(
    migrations_path: Path,
    name: str,
) -> CreatedMigration:
    """Create a new migration file."""
    name = validate_migration_name(name)

    migrations_path = (
        migrations_path.expanduser().resolve()
    )

    try:
        migrations_path.mkdir(
            parents=True,
            exist_ok=True,
        )
    except OSError as exc:
        raise MigrationCreationError(
            f"Could not create migrations directory "
            f"'{migrations_path}': {exc}"
        ) from exc

    migrations = _load_existing_migrations(
        migrations_path
    )

    for migration in migrations:
        if migration.name == name:
            raise MigrationCreationError(
                f"Migration name '{name}' already exists "
                f"as version {migration.version:03d}."
            )

    version = _next_version(
        migrations
    )

    filename = (
        f"{version:03d}_{name}.sql"
    )

    path = migrations_path / filename

    if path.exists():
        raise MigrationCreationError(
            f"Migration file already exists: '{path}'."
        )

    content = _render_migration(
        version,
        name,
    )

    try:
        with path.open(
            "x",
            encoding="utf-8",
        ) as file:
            file.write(content)
    except FileExistsError as exc:
        raise MigrationCreationError(
            f"Migration file already exists: '{path}'."
        ) from exc
    except OSError as exc:
        raise MigrationCreationError(
            f"Could not create migration "
            f"'{path}': {exc}"
        ) from exc

    return CreatedMigration(
        version=version,
        name=name,
        path=path,
    )