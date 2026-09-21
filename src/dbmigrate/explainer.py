"""Migration SQL explanation."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Sequence

from .migration import Migration


class MigrationExplanationError(Exception):
    """Raised when migration explanation fails."""


@dataclass(frozen=True)
class Explanation:
    """Explain one SQL operation."""

    section: str
    line: int
    operation: str
    description: str

    def format(self) -> str:
        """Return a human-readable explanation."""
        return (
            f"{self.operation}\n"
            f"  line: {self.line}\n"
            f"  {self.description}"
        )


@dataclass(frozen=True)
class MigrationExplanation:
    """Explanation of a complete migration."""

    migration: Migration
    explanations: tuple[Explanation, ...]

    @property
    def is_empty(self) -> bool:
        """Return whether no SQL operations were recognized."""
        return not self.explanations


_OPERATION_PATTERNS = (
    (
        "CREATE_TABLE",
        re.compile(
            r"\bCREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?"
            r"([`\"\[]?[\w.]+[`\"\]]?)",
            re.IGNORECASE,
        ),
        "Creates table '{object}'.",
    ),
    (
        "DROP_TABLE",
        re.compile(
            r"\bDROP\s+TABLE\s+(?:IF\s+EXISTS\s+)?"
            r"([`\"\[]?[\w.]+[`\"\]]?)",
            re.IGNORECASE,
        ),
        "Removes table '{object}'.",
    ),
    (
        "ALTER_TABLE",
        re.compile(
            r"\bALTER\s+TABLE\s+([`\"\[]?[\w.]+[`\"\]]?)",
            re.IGNORECASE,
        ),
        "Changes the structure of table '{object}'.",
    ),
    (
        "CREATE_INDEX",
        re.compile(
            r"\bCREATE\s+(?:UNIQUE\s+)?INDEX\s+"
            r"([`\"\[]?[\w.]+[`\"\]]?)",
            re.IGNORECASE,
        ),
        "Creates index '{object}'.",
    ),
    (
        "DROP_INDEX",
        re.compile(
            r"\bDROP\s+INDEX\s+(?:IF\s+EXISTS\s+)?"
            r"([`\"\[]?[\w.]+[`\"\]]?)",
            re.IGNORECASE,
        ),
        "Removes index '{object}'.",
    ),
    (
        "INSERT",
        re.compile(
            r"\bINSERT\s+INTO\s+([`\"\[]?[\w.]+[`\"\]]?)",
            re.IGNORECASE,
        ),
        "Inserts data into table '{object}'.",
    ),
    (
        "UPDATE",
        re.compile(
            r"\bUPDATE\s+([`\"\[]?[\w.]+[`\"\]]?)",
            re.IGNORECASE,
        ),
        "Updates data in table '{object}'.",
    ),
    (
        "DELETE",
        re.compile(
            r"\bDELETE\s+FROM\s+([`\"\[]?[\w.]+[`\"\]]?)",
            re.IGNORECASE,
        ),
        "Deletes data from table '{object}'.",
    ),
)


def _clean_identifier(identifier: str) -> str:
    """Remove common SQL identifier quoting."""
    return identifier.strip(
        '`"[]'
    )


def _explain_section(
    section: str,
    sql: str,
) -> list[Explanation]:
    """Explain recognized operations in one SQL section."""
    explanations: list[Explanation] = []

    for line_number, line in enumerate(
        sql.splitlines(),
        start=1,
    ):
        stripped = line.strip()

        if not stripped:
            continue

        for operation, pattern, template in _OPERATION_PATTERNS:
            match = pattern.search(
                stripped
            )

            if match is None:
                continue

            object_name = _clean_identifier(
                match.group(1)
            )

            explanations.append(
                Explanation(
                    section=section,
                    line=line_number,
                    operation=operation,
                    description=template.format(
                        object=object_name
                    ),
                )
            )

            break

    return explanations


def explain_migration(
    migration: Migration,
) -> MigrationExplanation:
    """Explain recognized operations in one migration."""
    explanations: list[Explanation] = []

    explanations.extend(
        _explain_section(
            "up",
            migration.up_sql,
        )
    )

    explanations.extend(
        _explain_section(
            "down",
            migration.down_sql,
        )
    )

    return MigrationExplanation(
        migration=migration,
        explanations=tuple(
            explanations
        ),
    )


def explain_migrations(
    migrations: Sequence[Migration],
) -> tuple[MigrationExplanation, ...]:
    """Explain a collection of migrations."""
    ordered = sorted(
        migrations,
        key=lambda migration: migration.version,
    )

    return tuple(
        explain_migration(
            migration
        )
        for migration in ordered
    )