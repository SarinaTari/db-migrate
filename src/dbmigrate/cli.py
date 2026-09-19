"""Command-line interface for dbmigrate."""

from __future__ import annotations

import argparse
from typing import Sequence

from . import __version__
from .commands.base import Command, get_commands
from .config import ConfigurationError, load_config


DESCRIPTION = (
    "A database migration and schema-evolution CLI "
    "focused on safety, integrity, and explainability."
)


def build_parser() -> argparse.ArgumentParser:
    """Build and return the top-level argument parser."""
    parser = argparse.ArgumentParser(
        prog="dbmigrate",
        description=DESCRIPTION,
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        title="commands",
        metavar="<command>",
    )

    for command in get_commands():
        subparsers.add_parser(
            command.name,
            help=command.help,
            description=command.help,
        )

    return parser


def resolve_command(command_name: str | None) -> Command | None:
    """Resolve a command name to its command definition."""
    if command_name is None:
        return None

    for command in get_commands():
        if command.name == command_name:
            return command

    return None


def run_command(command: Command | None) -> int:
    """Execute a parsed command.

    Command behavior is intentionally limited at this stage.
    Configuration-aware commands will be implemented incrementally.
    """
    if command is None:
        return 0

    if command.name == "init":
        print(
            "The init command will be implemented in a later phase."
        )
        return 0

    try:
        config = load_config()
    except ConfigurationError as exc:
        print(f"Configuration error: {exc}")
        return 1

    print(
        f"Project: {config.project_root}"
    )
    print(
        f"Command '{command.name}' is not implemented yet. "
        "This command will be introduced in a later phase."
    )

    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the dbmigrate command-line interface."""
    parser = build_parser()
    args = parser.parse_args(argv)

    command = resolve_command(args.command)

    return run_command(command)


if __name__ == "__main__":
    raise SystemExit(main())