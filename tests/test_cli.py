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


def test_unimplemented_command_still_dispatches(
    tmp_path: Path,
    monkeypatch,
    capsys,
):
    monkeypatch.chdir(tmp_path)

    write_config(
        tmp_path / "dbmigrate.toml"
    )

    exit_code = main(["up"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "not implemented yet" in captured.out