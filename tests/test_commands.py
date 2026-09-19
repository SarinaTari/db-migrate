"""Tests for the CLI command definitions."""

from dbmigrate.commands.base import get_commands


def test_commands_are_defined() -> None:
    """The CLI should expose the planned command set."""
    commands = get_commands()

    assert commands


def test_command_names_are_unique() -> None:
    """Every command should have a unique name."""
    commands = get_commands()
    names = [command.name for command in commands]

    assert len(names) == len(set(names))


def test_required_commands_are_present() -> None:
    """The foundational CLI should register the planned commands."""
    commands = get_commands()
    names = {command.name for command in commands}

    expected = {
        "init",
        "create",
        "up",
        "down",
        "status",
        "history",
        "current",
        "validate",
        "plan",
        "lint",
        "explain",
        "impact",
        "schema",
        "schema-diff",
        "fingerprint",
        "doctor",
        "check",
        "verify-schema",
    }

    assert expected.issubset(names)


def test_commands_have_help_text() -> None:
    """Every command should have user-facing help text."""
    for command in get_commands():
        assert command.name
        assert command.help