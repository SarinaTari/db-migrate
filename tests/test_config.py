"""Tests for project configuration."""

from pathlib import Path

import pytest

from dbmigrate.config import (
    ConfigurationError,
    find_project_root,
    load_config,
)


def write_config(
    path: Path,
    content: str,
) -> None:
    path.write_text(
        content,
        encoding="utf-8",
    )


def test_load_default_config(tmp_path: Path):
    config_path = tmp_path / "dbmigrate.toml"

    write_config(
        config_path,
        """
[migrations]
directory = "migrations"

[database]
url = "sqlite:///dbmigrate.db"
""",
    )

    config = load_config(config_path)

    assert config.project_root == tmp_path
    assert config.migrations_dir == Path("migrations")
    assert config.migrations_path == tmp_path / "migrations"
    assert config.database_url == "sqlite:///dbmigrate.db"


def test_database_url_defaults_to_sqlite(tmp_path: Path):
    config_path = tmp_path / "dbmigrate.toml"

    write_config(
        config_path,
        """
[migrations]
directory = "migrations"
""",
    )

    config = load_config(config_path)

    assert config.database_url == "sqlite:///dbmigrate.db"


def test_find_project_root_from_nested_directory(
    tmp_path: Path,
):
    project_root = tmp_path / "project"
    nested = project_root / "src" / "nested"

    project_root.mkdir()
    nested.mkdir(parents=True)

    write_config(
        project_root / "dbmigrate.toml",
        """
[migrations]
directory = "migrations"

[database]
url = "sqlite:///database.db"
""",
    )

    assert find_project_root(nested) == project_root


def test_missing_config_raises_error(tmp_path: Path):
    with pytest.raises(
        ConfigurationError,
        match="does not exist",
    ):
        load_config(
            tmp_path / "dbmigrate.toml"
        )


def test_invalid_toml_raises_error(tmp_path: Path):
    config_path = tmp_path / "dbmigrate.toml"

    write_config(
        config_path,
        """
[migrations
directory = "migrations"
""",
    )

    with pytest.raises(
        ConfigurationError,
        match="Invalid TOML",
    ):
        load_config(config_path)


def test_invalid_migrations_directory_raises_error(
    tmp_path: Path,
):
    config_path = tmp_path / "dbmigrate.toml"

    write_config(
        config_path,
        """
[migrations]
directory = ""
""",
    )

    with pytest.raises(
        ConfigurationError,
        match="non-empty string",
    ):
        load_config(config_path)


def test_migrations_directory_cannot_escape_project_root(
    tmp_path: Path,
):
    config_path = tmp_path / "dbmigrate.toml"

    write_config(
        config_path,
        """
[migrations]
directory = "../outside"
""",
    )

    with pytest.raises(
        ConfigurationError,
        match="inside the project root",
    ):
        load_config(config_path)


def test_database_section_must_be_table(
    tmp_path: Path,
):
    config_path = tmp_path / "dbmigrate.toml"

    write_config(
        config_path,
        """
[migrations]
directory = "migrations"

database = "sqlite:///db.db"
""",
    )

    # This structure is actually a valid TOML key inside
    # [migrations], so it should not be interpreted as [database].
    config = load_config(config_path)

    assert config.database_url == "sqlite:///dbmigrate.db"


def test_database_url_must_be_non_empty(
    tmp_path: Path,
):
    config_path = tmp_path / "dbmigrate.toml"

    write_config(
        config_path,
        """
[migrations]
directory = "migrations"

[database]
url = ""
""",
    )

    with pytest.raises(
        ConfigurationError,
        match="database.url",
    ):
        load_config(config_path)