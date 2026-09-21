"""Migration file parsing and discovery."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


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
    """Base exception for migration errors."""


class MigrationParseError(MigrationError):
    """Raised when a migration file cannot be parsed."""


class MigrationDiscoveryError(MigrationError):
    """Raised when migrations cannot be discovered."""


@dataclass(frozen=True)
class Migration:
    """Represent one database migration."""

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


def _parse_filename(
    path: Path,
) -> tuple[int, str]:
    """Parse a migration version and name from its filename."""
    match = MIGRATION_FILENAME_PATTERN.fullmatch(
        path.name
    )

    if match is None:
        raise MigrationParseError(
            f"Invalid migration filename: {path.name}"
        )

    version = int(
        match.group("version")
    )
    name = match.group("name")

    if version <= 0:
        raise MigrationParseError(
            f"Migration version must be greater than zero: "
            f"{path.name}"
        )

    return version, name


def _parse_metadata(
    content: str,
    path: Path,
) -> tuple[int, str]:
    """Parse migration metadata from file contents."""
    migration_version: int | None = None
    migration_name: str | None = None

    for line in content.splitlines():
        if migration_version is None:
            version_match = MIGRATION_HEADER_PATTERN.match(
                line
            )

            if version_match is not None:
                migration_version = int(
                    version_match.group("version")
                )

        if migration_name is None:
            name_match = MIGRATION_NAME_PATTERN.match(
                line
            )

            if name_match is not None:
                migration_name = name_match.group(
                    "name"
                )

        if (
            migration_version is not None
            and migration_name is not None
        ):
            break

    if migration_version is None:
        raise MigrationParseError(
            f"migration metadata is missing a version: "
            f"{path.name}"
        )

    if migration_version <= 0:
        raise MigrationParseError(
            f"Migration version must be greater than zero: "
            f"{path.name}"
        )

    if migration_name is None:
        raise MigrationParseError(
            f"migration metadata is missing a name: "
            f"{path.name}"
        )

    return migration_version, migration_name


def _extract_sections(
    content: str,
    path: Path,
) -> tuple[str, str]:
    """Extract the up and down SQL sections."""
    lines = content.splitlines()

    up_index: int | None = None
    down_index: int | None = None

    for index, line in enumerate(lines):
        stripped = line.strip()

        if stripped == UP_MARKER:
            if up_index is not None:
                raise MigrationParseError(
                    f"migration must contain exactly one "
                    f"'{UP_MARKER}' marker: {path.name}"
                )

            up_index = index

        elif stripped == DOWN_MARKER:
            if down_index is not None:
                raise MigrationParseError(
                    f"migration must contain exactly one "
                    f"'{DOWN_MARKER}' marker: {path.name}"
                )

            down_index = index

    if up_index is None:
        raise MigrationParseError(
            f"migration must contain exactly one "
            f"'{UP_MARKER}' marker: {path.name}"
        )

    if down_index is None:
        raise MigrationParseError(
            f"migration must contain exactly one "
            f"'{DOWN_MARKER}' marker: {path.name}"
        )

    if down_index <= up_index:
        raise MigrationParseError(
            f"'{DOWN_MARKER}' marker appears before "
            f"'{UP_MARKER}': {path.name}"
        )

    up_sql = "\n".join(
        lines[up_index + 1:down_index]
    ).strip()

    down_sql = "\n".join(
        lines[down_index + 1:]
    ).strip()

    if not up_sql:
        raise MigrationParseError(
            f"empty up section: {path.name}"
        )

    if not down_sql:
        raise MigrationParseError(
            f"empty down section: {path.name}"
        )

    return up_sql, down_sql


def parse_migration(
    path: Path,
) -> Migration:
    """Parse one migration file."""
    path = Path(path).resolve()

    if not path.exists():
        raise MigrationParseError(
            f"Migration file does not exist: {path}"
        )

    if not path.is_file():
        raise MigrationParseError(
            f"Migration path is not a file: {path}"
        )

    if path.suffix.lower() != ".sql":
        raise MigrationParseError(
            f"Migration file must use the .sql extension: "
            f"{path.name}"
        )

    version_from_filename, name_from_filename = (
        _parse_filename(path)
    )

    try:
        content = path.read_text(
            encoding="utf-8"
        )
    except OSError as exc:
        raise MigrationParseError(
            f"Could not read migration file "
            f"{path.name}: {exc}"
        ) from exc

    version_from_metadata, name_from_metadata = (
        _parse_metadata(
            content,
            path,
        )
    )

    if version_from_filename != version_from_metadata:
        raise MigrationParseError(
            f"Migration version mismatch in {path.name}: "
            f"filename declares {version_from_filename}, "
            f"metadata declares {version_from_metadata}."
        )

    if name_from_filename != name_from_metadata:
        raise MigrationParseError(
            f"Migration name mismatch in {path.name}: "
            f"filename declares '{name_from_filename}', "
            f"metadata declares '{name_from_metadata}'."
        )

    up_sql, down_sql = _extract_sections(
        content,
        path,
    )

    return Migration(
        version=version_from_filename,
        name=name_from_filename,
        up_sql=up_sql,
        down_sql=down_sql,
        path=path,
    )


def discover_migrations(
    directory: Path,
) -> tuple[Migration, ...]:
    """Discover and parse all migration files."""
    directory = Path(directory).resolve()

    if not directory.exists():
        raise MigrationDiscoveryError(
            f"Migration directory does not exist: "
            f"{directory}"
        )

    if not directory.is_dir():
        raise MigrationDiscoveryError(
            f"Migration path is not a directory: "
            f"{directory}"
        )

    try:
        migration_paths = sorted(
            directory.glob("*.sql"),
            key=lambda path: path.name,
        )
    except OSError as exc:
        raise MigrationDiscoveryError(
            f"Could not inspect migration directory "
            f"{directory}: {exc}"
        ) from exc

    migrations: list[Migration] = []

    for path in migration_paths:
        try:
            migrations.append(
                parse_migration(path)
            )
        except MigrationParseError as exc:
            raise MigrationDiscoveryError(
                str(exc)
            ) from exc

    migrations.sort(
        key=lambda migration: migration.version
    )

    versions: set[int] = set()

    for migration in migrations:
        if migration.version in versions:
            raise MigrationDiscoveryError(
                f"Duplicate migration version "
                f"{migration.version:03d}."
            )

        versions.add(
            migration.version
        )

    return tuple(migrations)