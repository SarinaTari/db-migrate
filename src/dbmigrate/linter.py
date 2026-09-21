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


def _statement_lines(
    sql: str,
) -> list[tuple[int, str]]:
    """Return non-empty SQL lines with their original numbers."""
    return [
        (line_number, line)
        for line_number, line in enumerate(
            sql.splitlines(),
            start=1,
        )
        if line.strip()
    ]


def _has_where_after(
    lines: list[tuple[int, str]],
    index: int,
) -> bool:
    """Return whether WHERE appears in the current statement."""
    statement: list[str] = []

    for _, line in lines[index:]:
        statement.append(line)

        if ";" in line:
            break

    return bool(
        re.search(
            r"\bWHERE\b",
            "\n".join(statement),
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
    issues: list[LintIssue] = []

    for index, (line_number, line) in enumerate(lines):
        for rule in _RULES:
            if not rule.pattern.search(line):
                continue

            if rule.code == "DELETE_NO_WHERE":
                if _has_where_after(lines, index):
                    continue

            if rule.code == "UPDATE_NO_WHERE":
                if _has_where_after(lines, index):
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