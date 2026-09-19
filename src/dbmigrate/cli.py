"""Command-line interface for dbmigrate."""

from __future__ import annotations

import argparse

from . import __version__


def build_parser() -> argparse.ArgumentParser:
    """Build and return the top-level argument parser."""
    parser = argparse.ArgumentParser(
        prog="dbmigrate",
        description=(
            "A database migration and schema-evolution CLI "
            "focused on safety, integrity, and explainability."
        ),
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    return parser


def main() -> int:
    """Run the dbmigrate command-line interface."""
    parser = build_parser()
    parser.parse_args()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())