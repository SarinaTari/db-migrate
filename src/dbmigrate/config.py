"""Project configuration loading for dbmigrate."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib


DEFAULT_CONFIG_FILENAME = "dbmigrate.toml"


class ConfigurationError(Exception):
    """Raised when project configuration is invalid."""


@dataclass(frozen=True)
class ProjectConfig:
    """Configuration for a dbmigrate project."""

    project_root: Path
    migrations_dir: Path
    config_path: Path

    @property
    def migrations_path(self) -> Path:
        """Return the absolute path to the migrations directory."""
        return self.project_root / self.migrations_dir


def find_project_root(start: Path | None = None) -> Path:
    """Find the nearest directory containing dbmigrate.toml."""
    current = (start or Path.cwd()).resolve()

    if current.is_file():
        current = current.parent

    for directory in (current, *current.parents):
        config_path = directory / DEFAULT_CONFIG_FILENAME

        if config_path.is_file():
            return directory

    raise ConfigurationError(
        f"Could not find {DEFAULT_CONFIG_FILENAME} starting from '{current}'."
    )


def load_config(path: Path | None = None) -> ProjectConfig:
    """Load and validate a dbmigrate project configuration."""

    if path is None:
        project_root = find_project_root()
        config_path = project_root / DEFAULT_CONFIG_FILENAME
    else:
        config_path = path.expanduser().resolve()

        if not config_path.is_file():
            raise ConfigurationError(
                f"Configuration file does not exist: '{config_path}'."
            )

        project_root = config_path.parent

    try:
        with config_path.open("rb") as file:
            data = tomllib.load(file)

    except tomllib.TOMLDecodeError as exc:
        raise ConfigurationError(
            f"Invalid TOML in '{config_path}': {exc}"
        ) from exc

    except OSError as exc:
        raise ConfigurationError(
            f"Could not read configuration file '{config_path}': {exc}"
        ) from exc

    migrations_config = data.get("migrations", {})

    if not isinstance(migrations_config, dict):
        raise ConfigurationError(
            "The [migrations] configuration must be a table."
        )

    migrations_dir = migrations_config.get(
        "directory",
        "migrations",
    )

    if not isinstance(migrations_dir, str) or not migrations_dir.strip():
        raise ConfigurationError(
            "The migrations.directory setting must be a non-empty string."
        )

    migrations_path = (project_root / migrations_dir).resolve()

    try:
        migrations_path.relative_to(project_root)
    except ValueError as exc:
        raise ConfigurationError(
            "The migrations directory must be inside the project root."
        ) from exc

    return ProjectConfig(
        project_root=project_root,
        migrations_dir=Path(migrations_dir),
        config_path=config_path,
    )