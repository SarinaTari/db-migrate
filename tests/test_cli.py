"""Tests for the dbmigrate CLI."""

from __future__ import annotations

from dbmigrate import __version__
from dbmigrate.cli import build_parser, main, resolve_command


def test_parser_accepts_known_command():
    parser = build_parser()

    args = parser.parse_args(["status"])

    assert args.command == "status"


def test_parser_accepts_version_flag(capsys):
    try:
        main(["--version"])
    except SystemExit as exc:
        assert exc.code == 0

    captured = capsys.readouterr()

    assert f"dbmigrate {__version__}" in captured.out


def test_parser_help(capsys):
    try:
        main(["--help"])
    except SystemExit as exc:
        assert exc.code == 0

    captured = capsys.readouterr()

    assert "dbmigrate" in captured.out
    assert "status" in captured.out
    assert "create" in captured.out


def test_no_command_prints_help(capsys):
    exit_code = main([])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "usage:" in captured.out
    assert "dbmigrate" in captured.out


def test_resolve_known_command():
    command = resolve_command("status")

    assert command is not None
    assert command.name == "status"


def test_resolve_unknown_command():
    assert resolve_command("does-not-exist") is None


def test_command_requires_configuration(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)

    exit_code = main(["status"])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Configuration error" in captured.out


def test_init_does_not_require_configuration(
    monkeypatch,
    tmp_path,
    capsys,
):
    monkeypatch.chdir(tmp_path)

    exit_code = main(["init"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "later phase" in captured.out


def test_command_uses_project_configuration(
    monkeypatch,
    tmp_path,
    capsys,
):
    monkeypatch.chdir(tmp_path)

    (tmp_path / "dbmigrate.toml").write_text(
        '[migrations]\ndirectory = "migrations"\n',
        encoding="utf-8",
    )

    exit_code = main(["status"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert f"Project root: {tmp_path}" in captured.out
    assert "status" in captured.out