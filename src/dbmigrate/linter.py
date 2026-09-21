"""Migration SQL linting."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Sequence

from .migration import Migration


class MigrationLintError(Exception):
    """Raised when migration linting fails."""


@dataclass(frozen=True)
class LintIssue:
    """Describe a single migration lint issue."""

    migration: Migration
    section: str
    line: int
    code: str
    severity: str
    message: str

    @property
    def version(self) -> int:
        """Return the migration version."""
        return self.migration.version

    @property
    def identifier(self) -> str:
        """Return the migration identifier."""
        return self.migration.identifier

    def format(self) -> str:
        """Return a human-readable issue description."""
        return (
            f"{self.severity} [{self.code}] "
            f"{self.identifier} "
            f"{self.section}: line {self.line} "
            f"{self.message}"
        )


@dataclass(frozen=True)
class LintReport:
    """Collection of migration lint issues."""

    migrations: tuple[Migration, ...]
    issues: tuple[LintIssue, ...]

    @property
    def error_count(self) -> int:
        """Return the number of errors."""
        return sum(
            issue.severity == "ERROR"
            for issue in self.issues
        )

    @property
    def warning_count(self) -> int:
        """Return the number of warnings."""
        return sum(
            issue.severity == "WARNING"
            for issue in self.issues
        )

    @property
    def info_count(self) -> int:
        """Return the number of informational issues."""
        return sum(
            issue.severity == "INFO"
            for issue in self.issues
        )

    @property
    def is_clean(self) -> bool:
        """Return whether no lint issues were found."""
        return not self.issues

    @property
    def is_valid(self) -> bool:
        """Return whether no error-level issues were found."""
        return self.error_count == 0


@dataclass(frozen=True)
class _LintRule:
    """Internal representation of a lint rule."""

    code: str
    severity: str
    pattern: re.Pattern[str]
    message: str


_RULES = (
    _LintRule(
        code="DROP_TABLE",
        severity="ERROR",
        pattern=re.compile(
            r"\bDROP\s+TABLE\b",
            re.IGNORECASE,
        ),
        message=(
            "DROP TABLE removes an existing table "
            "and can cause irreversible data loss."
        ),
    ),
    _LintRule(
        code="DROP_COLUMN",
        severity="ERROR",
        pattern=re.compile(
            r"\bDROP\s+COLUMN\b",
            re.IGNORECASE,
        ),
        message=(
            "DROP COLUMN removes an existing column "
            "and can cause irreversible data loss."
        ),
    ),
    _LintRule(
        code="DELETE_NO_WHERE",
        severity="ERROR",
        pattern=re.compile(
            r"\bDELETE\s+FROM\b",
            re.IGNORECASE,
        ),
        message=(
            "DELETE without WHERE can remove every row "
            "from the target table."
        ),
    ),
    _LintRule(
        code="UPDATE_NO_WHERE",
        severity="WARNING",
        pattern=re.compile(
            r"\bUPDATE\b",
            re.IGNORECASE,
        ),
        message=(
            "UPDATE without WHERE can modify every row "
            "in the target table."
        ),
    ),
    _LintRule(
        code="ALTER_TABLE",
        severity="WARNING",
        pattern=re.compile(
            r"\bALTER\s+TABLE\b",
            re.IGNORECASE,
        ),
        message=(
            "ALTER TABLE changes an existing database "
            "schema and should be reviewed carefully."
        ),
    ),
    _LintRule(
        code="CREATE_INDEX",
        severity="INFO",
        pattern=re.compile(
            r"\bCREATE\s+(?:UNIQUE\s+)?INDEX\b",
            re.IGNORECASE,
        ),
        message=(
            "CREATE INDEX changes database structure "
            "and may affect storage and write performance."
        ),
    ),
)


def _mask_sql_comments_and_literals(sql: str) -> str:
    """
    Mask SQL comments and quoted literals while preserving line structure.

    The returned string has the same number of lines as the input, allowing
    lint issues to retain their original source line numbers. SQL keywords
    inside comments and quoted values/identifiers are replaced with spaces so
    they cannot be mistaken for SQL operations.
    """
    result: list[str] = []
    index = 0
    length = len(sql)

    while index < length:
        char = sql[index]

        if char == "-" and index + 1 < length and sql[index + 1] == "-":
            result.extend((" ", " "))
            index += 2

            while index < length and sql[index] != "\n":
                result.append(" ")
                index += 1

            continue

        if char == "/" and index + 1 < length and sql[index + 1] == "*":
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
) -> list[tuple[int, str, str]]:
    """
    Return non-empty SQL lines with original and analysis-safe content.

    Each tuple contains:
        (original line number, original line, masked line)
    """
    masked_sql = _mask_sql_comments_and_literals(sql)

    original_lines = sql.splitlines()
    masked_lines = masked_sql.splitlines()

    lines: list[tuple[int, str, str]] = []

    for line_number, (original, masked) in enumerate(
        zip(original_lines, masked_lines),
        start=1,
    ):
        if masked.strip():
            lines.append(
                (
                    line_number,
                    original,
                    masked,
                )
            )

    return lines


def _statements_from_lines(
    lines: list[tuple[int, str, str]],
) -> list[tuple[int, str]]:
    """
    Split analysis-safe SQL into statements.

    The returned line number is the first source line of each statement.
    Statement splitting is intentionally lightweight and semicolon-based.
    """
    statements: list[tuple[int, str]] = []

    current: list[str] = []
    start_line: int | None = None

    for line_number, _, masked_line in lines:
        if start_line is None:
            start_line = line_number

        current.append(masked_line)

        parts = masked_line.split(";")

        if len(parts) == 1:
            continue

        for part in parts[:-1]:
            statement = "\n".join(current[:-1] + [part]).strip()

            if statement:
                statements.append(
                    (
                        start_line,
                        statement,
                    )
                )

            current = []
            start_line = None

        remainder = parts[-1]

        if remainder.strip():
            current = [remainder]
            if start_line is None:
                start_line = line_number

    if current:
        statement = "\n".join(current).strip()

        if statement and start_line is not None:
            statements.append(
                (
                    start_line,
                    statement,
                )
            )

    return statements


def _has_where(
    statement: str,
) -> bool:
    """Return whether WHERE appears in the current SQL statement."""
    return bool(
        re.search(
            r"\bWHERE\b",
            statement,
            re.IGNORECASE,
        )
    )


def _lint_section(
    migration: Migration,
    section: str,
    sql: str,
) -> list[LintIssue]:
    """Lint one migration SQL section."""
    lines = _statement_lines(sql)
    statements = _statements_from_lines(lines)

    issues: list[LintIssue] = []

    for line_number, statement in statements:
        for rule in _RULES:
            if not rule.pattern.search(statement):
                continue

            if rule.code in {
                "DELETE_NO_WHERE",
                "UPDATE_NO_WHERE",
            } and _has_where(statement):
                continue

            issues.append(
                LintIssue(
                    migration=migration,
                    section=section,
                    line=line_number,
                    code=rule.code,
                    severity=rule.severity,
                    message=rule.message,
                )
            )

    return issues


def lint_migration(
    migration: Migration,
) -> list[LintIssue]:
    """Lint one migration."""
    issues: list[LintIssue] = []

    issues.extend(
        _lint_section(
            migration,
            "up",
            migration.up_sql,
        )
    )

    issues.extend(
        _lint_section(
            migration,
            "down",
            migration.down_sql,
        )
    )

    return issues


def lint_migrations(
    migrations: Sequence[Migration],
) -> LintReport:
    """Lint a collection of migrations."""
    ordered_migrations = tuple(
        sorted(
            migrations,
            key=lambda migration: migration.version,
        )
    )

    issues: list[LintIssue] = []

    for migration in ordered_migrations:
        issues.extend(
            lint_migration(migration)
        )

    return LintReport(
        migrations=ordered_migrations,
        issues=tuple(issues),
    )