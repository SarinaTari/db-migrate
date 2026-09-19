"""Tests for the dbmigrate command-line interface."""

import pytest

from dbmigrate import __version__
from dbmigrate.cli import build_parser, main


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


def test_main_returns_success() -> None:
    """The CLI should return a successful exit code."""
    assert main() == 0