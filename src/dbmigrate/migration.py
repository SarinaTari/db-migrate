"""Migration models, parsing, validation, and discovery."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


MIGRATION_FILENAME_PATTERN = re.compile(
    r"^(?P<version>\d+)_(?P<name>[a-z0-9][a-z0-9_-]*)\.sql$"
)

MIGRATION_HEADER_PATTERN = re.compile(
    r"^\s*--\s*migration:\s*(?P<version>\d+)\s*$"
)

MIGRATION_NAME_PATTERN = re.compile(
    r"^\s*--\s*name:\s*(?P<name>[a-z0-9][a-z0-9_-]*)\s*$"
)

UP_MARKER = "-- +up"
DOWN_MARKER = "-- +down"


class MigrationError(Exception):
    """Base exception for migration-related errors."""


class MigrationParseError(MigrationError):
    """Raised when a migration file cannot be parsed."""


class MigrationDiscoveryError(MigrationError):
    """Raised when migrations cannot be discovered safely."""


@dataclass(frozen=True)
class Migration:
    """A parsed database migration."""

    version: int
    name: str
    up_sql: str
    down_sql: str
    path: Path

    @property
    def identifier(self) -> str:
        """Return the migration identifier."""
        return f"{self.version:03d}_{self.name}"

    @property
    def filename(self) -> str:
        """Return the migration filename."""
        return self.path.name


def _parse_filename(path: Path) -> tuple[int, str]:
    """Parse a migration version and name from its filename."""
    match = MIGRATION_FILENAME_PATTERN.fullmatch(path.name)

    if match is None:
        raise MigrationParseError(
            f"Invalid migration filename '{path.name}'. "
            "Expected '<version>_<name>.sql'."
        )

    version = int(match.group("version"))
    name = match.group("name")

    if version < 1:
        raise MigrationParseError(
            f"Migration version must be greater than zero: '{path.name}'."
        )

    return version, name


def _parse_metadata(lines: list[str], path: Path) -> tuple[int, str]:
    """Parse and validate migration metadata."""
    if len(lines) < 2:
        raise MigrationParseError(
            f"Migration '{path.name}' is missing required metadata."
        )

    version_match = MIGRATION_HEADER_PATTERN.match(lines[0])

    if version_match is None:
        raise MigrationParseError(
            f"Migration '{path.name}' must start with "
            "'-- migration: <version>'."
        )

    name_match = MIGRATION_NAME_PATTERN.match(lines[1])

    if name_match is None:
        raise MigrationParseError(
            f"Migration '{path.name}' must contain "
            "'-- name: <name>' immediately after the migration version."
        )

    version = int(version_match.group("version"))
    name = name_match.group("name")

    if version < 1:
        raise MigrationParseError(
            f"Migration version must be greater than zero: '{path.name}'."
        )

    return version, name


def _extract_sections(
    lines: list[str],
    path: Path,
) -> tuple[str, str]:
    """Extract the up and down SQL sections."""
    up_indices = [
        index
        for index, line in enumerate(lines)
        if line.strip() == UP_MARKER
    ]

    down_indices = [
        index
        for index, line in enumerate(lines)
        if line.strip() == DOWN_MARKER
    ]

    if len(up_indices) != 1:
        raise MigrationParseError(
            f"Migration '{path.name}' must contain exactly one "
            f"'{UP_MARKER}' marker."
        )

    if len(down_indices) != 1:
        raise MigrationParseError(
            f"Migration '{path.name}' must contain exactly one "
            f"'{DOWN_MARKER}' marker."
        )

    up_index = up_indices[0]
    down_index = down_indices[0]

    if up_index >= down_index:
        raise MigrationParseError(
            f"Migration '{path.name}' must place "
            f"'{UP_MARKER}' before '{DOWN_MARKER}'."
        )

    up_sql = "\n".join(lines[up_index + 1 : down_index]).strip()
    down_sql = "\n".join(lines[down_index + 1 :]).strip()

    if not up_sql:
        raise MigrationParseError(
            f"Migration '{path.name}' has an empty up section."
        )

    if not down_sql:
        raise MigrationParseError(
            f"Migration '{path.name}' has an empty down section."
        )

    return up_sql, down_sql


def parse_migration(path: Path) -> Migration:
    """Parse a migration file into a Migration object."""
    path = path.expanduser().resolve()

    if not path.is_file():
        raise MigrationParseError(
            f"Migration file does not exist: '{path}'."
        )

    if path.suffix != ".sql":
        raise MigrationParseError(
            f"Migration file must use the .sql extension: '{path.name}'."
        )

    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise MigrationParseError(
            f"Could not read migration '{path}': {exc}"
        ) from exc

    lines = content.splitlines()

    filename_version, filename_name = _parse_filename(path)
    metadata_version, metadata_name = _parse_metadata(lines, path)

    if filename_version != metadata_version:
        raise MigrationParseError(
            f"Migration version mismatch in '{path.name}': "
            f"filename has {filename_version}, "
            f"metadata has {metadata_version}."
        )

    if filename_name != metadata_name:
        raise MigrationParseError(
            f"Migration name mismatch in '{path.name}': "
            f"filename has '{filename_name}', "
            f"metadata has '{metadata_name}'."
        )

    up_sql, down_sql = _extract_sections(lines, path)

    return Migration(
        version=metadata_version,
        name=metadata_name,
        up_sql=up_sql,
        down_sql=down_sql,
        path=path,
    )


def discover_migrations(directory: Path) -> tuple[Migration, ...]:
    """Discover and parse all migration files in a directory."""
    directory = directory.expanduser().resolve()

    if not directory.exists():
        raise MigrationDiscoveryError(
            f"Migration directory does not exist: '{directory}'."
        )

    if not directory.is_dir():
        raise MigrationDiscoveryError(
            f"Migration path is not a directory: '{directory}'."
        )

    migration_files = sorted(directory.glob("*.sql"))

    migrations: list[Migration] = []

    for path in migration_files:
        migrations.append(parse_migration(path))

    migrations.sort(key=lambda migration: migration.version)

    seen_versions: set[int] = set()

    for migration in migrations:
        if migration.version in seen_versions:
            raise MigrationDiscoveryError(
                f"Duplicate migration version detected: "
                f"{migration.version:03d}."
            )

        seen_versions.add(migration.version)

    return tuple(migrations)