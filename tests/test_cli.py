"""Tests for the dbmigrate CLI."""

from pathlib import Path

from dbmigrate.cli import main


def write_config(
    path: Path,
    database_url: str = "sqlite:///dbmigrate.db",
) -> None:
    path.write_text(
        f"""
[migrations]
directory = "migrations"

[database]
url = "{database_url}"
""",
        encoding="utf-8",
    )


def test_version(capsys):
    exit_code = main(["--version"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out.strip() == "0.1.0"


def test_help(capsys):
    exit_code = main(["--help"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "dbmigrate" in captured.out
    assert "check" in captured.out
    assert "validate" in captured.out
    assert "up" in captured.out


def test_no_command_shows_help(capsys):
    exit_code = main([])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "usage:" in captured.out


def test_validate_requires_configuration(
    tmp_path: Path,
    monkeypatch,
    capsys,
):
    monkeypatch.chdir(tmp_path)

    exit_code = main(["validate"])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Configuration error" in captured.err


def test_check_requires_configuration(
    tmp_path: Path,
    monkeypatch,
    capsys,
):
    monkeypatch.chdir(tmp_path)

    exit_code = main(["check"])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Configuration error" in captured.err


def test_check_sqlite_database(
    tmp_path: Path,
    monkeypatch,
    capsys,
):
    monkeypatch.chdir(tmp_path)

    write_config(
        tmp_path / "dbmigrate.toml"
    )

    exit_code = main(["check"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Database connection: OK" in captured.out
    assert "Database engine: SQLite" in captured.out
    assert "SQLite version:" in captured.out


def test_check_rejects_non_sqlite_database(
    tmp_path: Path,
    monkeypatch,
    capsys,
):
    monkeypatch.chdir(tmp_path)

    write_config(
        tmp_path / "dbmigrate.toml",
        database_url="postgresql://localhost/example",
    )

    exit_code = main(["check"])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "supports only sqlite" in captured.err


def test_up_with_no_migrations_reports_no_pending(
    tmp_path: Path,
    monkeypatch,
    capsys,
):
    monkeypatch.chdir(tmp_path)

    write_config(
        tmp_path / "dbmigrate.toml"
    )

    (tmp_path / "migrations").mkdir()

    exit_code = main(["up"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "No pending migrations." in captured.out
    assert captured.err == ""


def test_down_with_no_applied_migrations(
    tmp_path: Path,
    monkeypatch,
    capsys,
):
    monkeypatch.chdir(tmp_path)

    write_config(
        tmp_path / "dbmigrate.toml"
    )

    (tmp_path / "migrations").mkdir()

    exit_code = main(["down"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "No applied migrations." in captured.out
    assert captured.err == ""


def test_down_rejects_invalid_steps(
    tmp_path: Path,
    monkeypatch,
    capsys,
):
    monkeypatch.chdir(tmp_path)

    write_config(
        tmp_path / "dbmigrate.toml"
    )

    exit_code = main(
        ["down", "--steps", "0"]
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "greater than zero" in captured.err


def test_history_with_no_applied_migrations(
    tmp_path: Path,
    monkeypatch,
    capsys,
):
    monkeypatch.chdir(tmp_path)

    write_config(
        tmp_path / "dbmigrate.toml"
    )

    (tmp_path / "migrations").mkdir()

    exit_code = main(["history"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "No migrations have been applied." in captured.out


def test_current_with_no_applied_migrations(
    tmp_path: Path,
    monkeypatch,
    capsys,
):
    monkeypatch.chdir(tmp_path)

    write_config(
        tmp_path / "dbmigrate.toml"
    )

    (tmp_path / "migrations").mkdir()

    exit_code = main(["current"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "No migrations have been applied." in captured.out

def test_status_with_no_migrations(
    tmp_path: Path,
    monkeypatch,
    capsys,
):
    monkeypatch.chdir(tmp_path)

    write_config(
        tmp_path / "dbmigrate.toml"
    )

    (tmp_path / "migrations").mkdir()

    exit_code = main(["status"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Migration status" in captured.out
    assert "Total migrations: 0" in captured.out
    assert "Applied: 0" in captured.out
    assert "Pending: 0" in captured.out
    assert "Missing: 0" in captured.out
    assert "Database is up to date." in captured.out


def test_status_reports_pending_migrations(
    tmp_path: Path,
    monkeypatch,
    capsys,
):
    monkeypatch.chdir(tmp_path)

    write_config(
        tmp_path / "dbmigrate.toml"
    )

    migrations_dir = (
        tmp_path / "migrations"
    )
    migrations_dir.mkdir()

    (migrations_dir / "001_create_users.sql").write_text(
        """-- migration: 001
-- name: create_users

-- +up

CREATE TABLE users (
    id INTEGER PRIMARY KEY
);

-- +down

DROP TABLE users;
""",
        encoding="utf-8",
    )

    exit_code = main(["status"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Pending: 1" in captured.out
    assert "001 create_users" in captured.out
    assert "Database requires migration changes." in captured.out


def test_status_requires_configuration(
    tmp_path: Path,
    monkeypatch,
    capsys,
):
    monkeypatch.chdir(tmp_path)

    exit_code = main(["status"])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Configuration error" in captured.err