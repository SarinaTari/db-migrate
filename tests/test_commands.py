"""Tests for command definitions."""

from dbmigrate.commands.base import (
    get_commands,
    resolve_command,
)


def test_commands_have_unique_names():
    commands = get_commands()
    names = [command.name for command in commands]

    assert len(names) == len(set(names))


def test_check_command_exists():
    command = resolve_command("check")

    assert command is not None
    assert command.name == "check"


def test_all_commands_have_descriptions():
    for command in get_commands():
        assert command.name
        assert command.description