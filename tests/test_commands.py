"""Tests for command definitions."""

from dbmigrate.commands.base import get_commands


def test_command_names_are_unique():
    commands = get_commands()

    names = [command.name for command in commands]

    assert len(names) == len(set(names))


def test_required_commands_exist():
    commands = get_commands()

    names = {command.name for command in commands}

    required = {
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

    assert required <= names


def test_commands_have_help_text():
    for command in get_commands():
        assert command.name
        assert command.help