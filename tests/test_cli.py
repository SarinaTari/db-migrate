"""Tests for the dbmigrate command-line interface."""

from __future__ import annotations

import pytest

from dbmigrate import __version__
from dbmigrate.cli import build_parser, main, resolve_command


def test_parser_program_name() -> None:
    """The CLI should use dbmigrate as its program name."""
    parser = build_parser()

    assert parser.prog == "dbmigrate"


def test_version_command() -> None:
    """The version command should exit successfully."""
    parser = build_parser()

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["--version"])

    assert exc_info.value.code == 0
    assert __version__ == "0.1.0"


def test_help_command() -> None:
    """The help option should exit successfully."""
    parser = build_parser()

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["--help"])

    assert exc_info.value.code == 0


def test_no_command_returns_success() -> None:
    """Running the CLI without a command should succeed."""
    assert main([]) == 0


def test_known_command_is_parsed() -> None:
    """A known command should be accepted by the parser."""
    parser = build_parser()

    args = parser.parse_args(["status"])

    assert args.command == "status"


def test_unknown_command_is_rejected() -> None:
    """Unknown commands should be rejected by argparse."""
    parser = build_parser()

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["does-not-exist"])

    assert exc_info.value.code != 0


def test_resolve_known_command() -> None:
    """Known command names should resolve to command definitions."""
    command = resolve_command("status")

    assert command is not None
    assert command.name == "status"


def test_resolve_unknown_command() -> None:
    """Unknown command names should not resolve."""
    assert resolve_command("does-not-exist") is None


def test_main_with_command_returns_success(capsys) -> None:
    """A recognized command should currently return successfully."""
    exit_code = main(["status"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "not implemented yet" in captured.out