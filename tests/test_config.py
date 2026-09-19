"""Tests for project configuration."""

from __future__ import annotations

from pathlib import Path

import pytest

from dbmigrate.config import (
    ConfigurationError,
    find_project_root,
    load_config,
)


def write_config(
    path: Path,
    content: str = '[migrations]\ndirectory = "migrations"\n',
) -> None:
    path.write_text(content, encoding="utf-8")


def test_load_config_uses_default_migrations_directory(tmp_path):
    config_path = tmp_path / "dbmigrate.toml"
    write_config(config_path)

    config = load_config(config_path)

    assert config.project_root == tmp_path
    assert config.migrations_dir == Path("migrations")
    assert config.migrations_path == tmp_path / "migrations"
    assert config.config_path == config_path


def test_load_config_supports_custom_migrations_directory(tmp_path):
    config_path = tmp_path / "dbmigrate.toml"

    write_config(
        config_path,
        '[migrations]\ndirectory = "database/migrations"\n',
    )

    config = load_config(config_path)

    assert config.migrations_dir == Path("database/migrations")
    assert config.migrations_path == (
        tmp_path / "database" / "migrations"
    )


def test_find_project_root_from_nested_directory(tmp_path):
    project_root = tmp_path / "project"
    nested = project_root / "src" / "module"

    nested.mkdir(parents=True)

    write_config(project_root / "dbmigrate.toml")

    assert find_project_root(nested) == project_root


def test_find_project_root_raises_when_missing(tmp_path):
    with pytest.raises(ConfigurationError, match="Could not find"):
        find_project_root(tmp_path)


def test_load_config_raises_for_missing_explicit_file(tmp_path):
    missing = tmp_path / "missing.toml"

    with pytest.raises(
        ConfigurationError,
        match="Configuration file does not exist",
    ):
        load_config(missing)


def test_load_config_rejects_invalid_toml(tmp_path):
    config_path = tmp_path / "dbmigrate.toml"

    config_path.write_text(
        "[migrations\n"
        'directory = "migrations"\n',
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError, match="Invalid TOML"):
        load_config(config_path)


def test_load_config_rejects_empty_migrations_directory(tmp_path):
    config_path = tmp_path / "dbmigrate.toml"

    write_config(
        config_path,
        '[migrations]\ndirectory = ""\n',
    )

    with pytest.raises(
        ConfigurationError,
        match="non-empty string",
    ):
        load_config(config_path)


def test_load_config_rejects_non_string_migrations_directory(tmp_path):
    config_path = tmp_path / "dbmigrate.toml"

    write_config(
        config_path,
        "[migrations]\ndirectory = 123\n",
    )

    with pytest.raises(
        ConfigurationError,
        match="non-empty string",
    ):
        load_config(config_path)


def test_load_config_rejects_path_outside_project_root(tmp_path):
    config_path = tmp_path / "dbmigrate.toml"

    write_config(
        config_path,
        '[migrations]\ndirectory = "../../outside"\n',
    )

    with pytest.raises(
        ConfigurationError,
        match="inside the project root",
    ):
        load_config(config_path)


def test_load_config_rejects_invalid_migrations_table(tmp_path):
    config_path = tmp_path / "dbmigrate.toml"

    write_config(
        config_path,
        'migrations = "migrations"\n',
    )

    with pytest.raises(
        ConfigurationError,
        match="must be a table",
    ):
        load_config(config_path)