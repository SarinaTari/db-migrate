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
            r"([\`\"\[]?[\w.]+[\`\"\]]?)",
            re.IGNORECASE,
        ),
        "Creates table '{object}'.",
    ),
    (
        "DROP_TABLE",
        re.compile(
            r"\bDROP\s+TABLE\s+(?:IF\s+EXISTS\s+)?"
            r"([\`\"\[]?[\w.]+[\`\"\]]?)",
            re.IGNORECASE,
        ),
        "Removes table '{object}'.",
    ),
    (
        "ALTER_TABLE",
        re.compile(
            r"\bALTER\s+TABLE\s+([\`\"\[]?[\w.]+[\`\"\]]?)",
            re.IGNORECASE,
        ),
        "Changes the structure of table '{object}'.",
    ),
    (
        "CREATE_INDEX",
        re.compile(
            r"\bCREATE\s+(?:UNIQUE\s+)?INDEX\s+"
            r"([\`\"\[]?[\w.]+[\`\"\]]?)",
            re.IGNORECASE,
        ),
        "Creates index '{object}'.",
    ),
    (
        "DROP_INDEX",
        re.compile(
            r"\bDROP\s+INDEX\s+(?:IF\s+EXISTS\s+)?"
            r"([\`\"\[]?[\w.]+[\`\"\]]?)",
            re.IGNORECASE,
        ),
        "Removes index '{object}'.",
    ),
    (
        "INSERT",
        re.compile(
            r"\bINSERT\s+INTO\s+([\`\"\[]?[\w.]+[\`\"\]]?)",
            re.IGNORECASE,
        ),
        "Inserts data into table '{object}'.",
    ),
    (
        "UPDATE",
        re.compile(
            r"\bUPDATE\s+([\`\"\[]?[\w.]+[\`\"\]]?)",
            re.IGNORECASE,
        ),
        "Updates data in table '{object}'.",
    ),
    (
        "DELETE",
        re.compile(
            r"\bDELETE\s+FROM\s+([\`\"\[]?[\w.]+[\`\"\]]?)",
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


def _mask_sql_comments_and_literals(sql: str) -> str:
    """
    Mask SQL comments and quoted literals while preserving line structure.

    SQL keywords inside comments or quoted values/identifiers are replaced
    with spaces so they cannot be mistaken for operations.
    """
    result: list[str] = []
    index = 0
    length = len(sql)

    while index < length:
        char = sql[index]

        if (
            char == "-"
            and index + 1 < length
            and sql[index + 1] == "-"
        ):
            result.extend((" ", " "))
            index += 2

            while index < length and sql[index] != "\n":
                result.append(" ")
                index += 1

            continue

        if (
            char == "/"
            and index + 1 < length
            and sql[index + 1] == "*"
        ):
            result.extend((" ", " "))
            index += 2

            while index < length:
                if (
                    sql[index] == "*"
                    and index + 1 < length
                    and sql[index + 1] == "/"
                ):
                    result.extend((" ", " "))
                    index += 2
                    break

                if sql[index] == "\n":
                    result.append("\n")
                else:
                    result.append(" ")

                index += 1

            continue

        if char in ("'", '"', "`"):
            quote = char
            result.append(" ")
            index += 1

            while index < length:
                current = sql[index]

                if current == "\n":
                    result.append("\n")
                    index += 1
                    continue

                if current == quote:
                    if (
                        index + 1 < length
                        and sql[index + 1] == quote
                    ):
                        result.extend((" ", " "))
                        index += 2
                        continue

                    result.append(" ")
                    index += 1
                    break

                result.append(" ")
                index += 1

            continue

        if char == "[":
            result.append(" ")
            index += 1

            while index < length:
                current = sql[index]

                if current == "\n":
                    result.append("\n")
                    index += 1
                    continue

                if current == "]":
                    result.append(" ")
                    index += 1
                    break

                result.append(" ")
                index += 1

            continue

        result.append(char)
        index += 1

    return "".join(result)


def _statement_lines(
    sql: str,
) -> list[tuple[int, str]]:
    """Return non-empty SQL lines with their original numbers."""
    masked_sql = _mask_sql_comments_and_literals(sql)

    return [
        (line_number, line)
        for line_number, line in enumerate(
            masked_sql.splitlines(),
            start=1,
        )
        if line.strip()
    ]


def _statements_from_lines(
    lines: list[tuple[int, str]],
) -> list[tuple[int, str]]:
    """
    Split SQL into statements.

    The returned line number is the first source line of each statement.
    Statement splitting is intentionally lightweight and semicolon-based.
    """
    statements: list[tuple[int, str]] = []

    current: list[str] = []
    start_line: int | None = None

    for line_number, line in lines:
        if start_line is None:
            start_line = line_number

        parts = line.split(";")

        if len(parts) == 1:
            current.append(line)
            continue

        if current:
            current.append(parts[0])
        else:
            current = [parts[0]]

        statement = "\n".join(current).strip()

        if statement and start_line is not None:
            statements.append(
                (
                    start_line,
                    statement,
                )
            )

        current = []
        start_line = None

        for part in parts[1:-1]:
            if part.strip():
                statements.append(
                    (
                        line_number,
                        part.strip(),
                    )
                )

        if parts[-1].strip():
            current = [parts[-1]]
            start_line = line_number

    if current and start_line is not None:
        statement = "\n".join(current).strip()

        if statement:
            statements.append(
                (
                    start_line,
                    statement,
                )
            )

    return statements


def _explain_section(
    section: str,
    sql: str,
) -> list[Explanation]:
    """Explain recognized operations in one SQL section."""
    lines = _statement_lines(sql)
    statements = _statements_from_lines(lines)

    explanations: list[Explanation] = []

    for line_number, statement in statements:
        for operation, pattern, template in _OPERATION_PATTERNS:
            match = pattern.search(statement)

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