"""Migration impact analysis."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Sequence

from .migration import Migration


class MigrationImpactError(Exception):
    """Raised when migration impact analysis fails."""


@dataclass(frozen=True)
class Impact:
    """Describe the apparent impact of one migration."""

    migration: Migration
    tables: tuple[str, ...]
    indexes: tuple[str, ...]
    operations: tuple[str, ...]
    risk: str

    @property
    def is_destructive(self) -> bool:
        """Return whether the migration contains destructive operations."""
        return self.risk == "HIGH"


_TABLE_PATTERNS = (
    re.compile(
        r"\bCREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?"
        r"([`\"\[]?[\w.]+[`\"\]]?)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bDROP\s+TABLE\s+(?:IF\s+EXISTS\s+)?"
        r"([`\"\[]?[\w.]+[`\"\]]?)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bALTER\s+TABLE\s+([`\"\[]?[\w.]+[`\"\]]?)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bINSERT\s+INTO\s+([`\"\[]?[\w.]+[`\"\]]?)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bUPDATE\s+([`\"\[]?[\w.]+[`\"\]]?)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bDELETE\s+FROM\s+([`\"\[]?[\w.]+[`\"\]]?)",
        re.IGNORECASE,
    ),
)


_INDEX_PATTERNS = (
    re.compile(
        r"\bCREATE\s+(?:UNIQUE\s+)?INDEX\s+"
        r"([`\"\[]?[\w.]+[`\"\]]?)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bDROP\s+INDEX\s+(?:IF\s+EXISTS\s+)?"
        r"([`\"\[]?[\w.]+[`\"\]]?)",
        re.IGNORECASE,
    ),
)


_OPERATION_PATTERNS = (
    (
        "CREATE_TABLE",
        re.compile(
            r"\bCREATE\s+TABLE\b",
            re.IGNORECASE,
        ),
    ),
    (
        "DROP_TABLE",
        re.compile(
            r"\bDROP\s+TABLE\b",
            re.IGNORECASE,
        ),
    ),
    (
        "ALTER_TABLE",
        re.compile(
            r"\bALTER\s+TABLE\b",
            re.IGNORECASE,
        ),
    ),
    (
        "CREATE_INDEX",
        re.compile(
            r"\bCREATE\s+(?:UNIQUE\s+)?INDEX\b",
            re.IGNORECASE,
        ),
    ),
    (
        "DROP_INDEX",
        re.compile(
            r"\bDROP\s+INDEX\b",
            re.IGNORECASE,
        ),
    ),
    (
        "INSERT",
        re.compile(
            r"\bINSERT\s+INTO\b",
            re.IGNORECASE,
        ),
    ),
    (
        "UPDATE",
        re.compile(
            r"\bUPDATE\b",
            re.IGNORECASE,
        ),
    ),
    (
        "DELETE",
        re.compile(
            r"\bDELETE\s+FROM\b",
            re.IGNORECASE,
        ),
    ),
)


def _clean_identifier(
    identifier: str,
) -> str:
    """Remove common SQL identifier quoting."""
    return identifier.strip(
        '`"[]'
    )


def _collect_objects(
    sql: str,
) -> tuple[set[str], set[str]]:
    """Collect apparent table and index references."""
    tables: set[str] = set()
    indexes: set[str] = set()

    for pattern in _TABLE_PATTERNS:
        for match in pattern.finditer(sql):
            tables.add(
                _clean_identifier(
                    match.group(1)
                )
            )

    for pattern in _INDEX_PATTERNS:
        for match in pattern.finditer(sql):
            indexes.add(
                _clean_identifier(
                    match.group(1)
                )
            )

    return tables, indexes


def _collect_operations(
    sql: str,
) -> set[str]:
    """Collect recognized SQL operation types."""
    operations: set[str] = set()

    for operation, pattern in _OPERATION_PATTERNS:
        if pattern.search(sql):
            operations.add(operation)

    return operations


def _risk_for_operations(
    operations: set[str],
) -> str:
    """Determine the highest apparent risk level."""
    if operations & {
        "DROP_TABLE",
        "DROP_INDEX",
    }:
        return "HIGH"

    if operations & {
        "ALTER_TABLE",
        "DELETE",
        "UPDATE",
    }:
        return "MEDIUM"

    return "INFO"


def analyze_migration_impact(
    migration: Migration,
) -> Impact:
    """Analyze the apparent impact of one migration."""
    sql = (
        migration.up_sql
        + "\n"
        + migration.down_sql
    )

    tables, indexes = _collect_objects(
        sql
    )

    operations = _collect_operations(
        sql
    )

    return Impact(
        migration=migration,
        tables=tuple(
            sorted(tables)
        ),
        indexes=tuple(
            sorted(indexes)
        ),
        operations=tuple(
            sorted(operations)
        ),
        risk=_risk_for_operations(
            operations
        ),
    )


def analyze_migrations(
    migrations: Sequence[Migration],
) -> tuple[Impact, ...]:
    """Analyze the apparent impact of migrations."""
    ordered = sorted(
        migrations,
        key=lambda migration: migration.version,
    )

    return tuple(
        analyze_migration_impact(
            migration
        )
        for migration in ordered
    )