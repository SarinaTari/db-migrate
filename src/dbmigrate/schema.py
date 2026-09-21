"""Database schema inspection and deterministic fingerprinting."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Any

from .database import Database, DatabaseError


class SchemaInspectionError(Exception):
    """Raised when database schema inspection fails."""


@dataclass(frozen=True)
class ColumnInfo:
    """Describe one database column."""

    name: str
    data_type: str
    not_null: bool
    default_value: str | None
    primary_key_position: int

    def normalized(self) -> str:
        """Return a deterministic representation of the column."""
        default = (
            ""
            if self.default_value is None
            else self.default_value
        )

        return (
            f"column|"
            f"{self.name}|"
            f"{self.data_type}|"
            f"{int(self.not_null)}|"
            f"{default}|"
            f"{self.primary_key_position}"
        )


@dataclass(frozen=True)
class IndexInfo:
    """Describe one database index."""

    name: str
    unique: bool
    columns: tuple[str, ...]

    def normalized(self) -> str:
        """Return a deterministic representation of the index."""
        columns = ",".join(self.columns)

        return (
            f"index|"
            f"{self.name}|"
            f"{int(self.unique)}|"
            f"{columns}"
        )


@dataclass(frozen=True)
class ForeignKeyInfo:
    """Describe one foreign-key relationship."""

    column: str
    referenced_table: str
    referenced_column: str
    on_update: str
    on_delete: str

    def normalized(self) -> str:
        """Return a deterministic representation of the foreign key."""
        return (
            f"foreign_key|"
            f"{self.column}|"
            f"{self.referenced_table}|"
            f"{self.referenced_column}|"
            f"{self.on_update}|"
            f"{self.on_delete}"
        )


@dataclass(frozen=True)
class TableInfo:
    """Describe one database table."""

    name: str
    columns: tuple[ColumnInfo, ...]
    indexes: tuple[IndexInfo, ...]
    foreign_keys: tuple[ForeignKeyInfo, ...]

    def normalized(self) -> tuple[str, ...]:
        """Return deterministic normalized table information."""
        lines = [
            f"table|{self.name}",
        ]

        lines.extend(
            column.normalized()
            for column in self.columns
        )

        lines.extend(
            index.normalized()
            for index in self.indexes
        )

        lines.extend(
            foreign_key.normalized()
            for foreign_key in self.foreign_keys
        )

        return tuple(lines)


@dataclass(frozen=True)
class ViewInfo:
    """Describe one database view."""

    name: str
    sql: str

    def normalized(self) -> str:
        """Return a deterministic representation of the view."""
        return f"view|{self.name}|{_normalize_sql(self.sql)}"


@dataclass(frozen=True)
class DatabaseSchema:
    """Represent the inspected database schema."""

    tables: tuple[TableInfo, ...]
    views: tuple[ViewInfo, ...]

    @property
    def table_count(self) -> int:
        """Return the number of tables."""
        return len(self.tables)

    @property
    def view_count(self) -> int:
        """Return the number of views."""
        return len(self.views)

    @property
    def is_empty(self) -> bool:
        """Return whether the database contains no user schema objects."""
        return not self.tables and not self.views

    def normalized(self) -> tuple[str, ...]:
        """Return the complete deterministic schema representation."""
        lines: list[str] = []

        for table in self.tables:
            lines.extend(table.normalized())

        for view in self.views:
            lines.append(view.normalized())

        return tuple(lines)

    def fingerprint(self) -> str:
        """Return the SHA-256 fingerprint of the normalized schema."""
        content = "\n".join(
            self.normalized()
        )

        return hashlib.sha256(
            content.encode("utf-8")
        ).hexdigest()


def _normalize_sql(sql: str) -> str:
    """Normalize SQL whitespace for deterministic comparison."""
    return " ".join(
        sql.split()
    )


def _row_value(
    row: Any,
    key: str,
    index: int,
) -> Any:
    """Read a value from either a mapping-like or tuple-like row."""
    try:
        return row[key]
    except (
        KeyError,
        IndexError,
        TypeError,
    ):
        return row[index]


def _database_objects(
    database: Any,
    object_type: str,
) -> list[tuple[str, str]]:
    """Return user-defined SQLite objects of one type."""
    try:
        rows = database.fetch_all(
            """
            SELECT name, sql
            FROM sqlite_master
            WHERE type = ?
              AND name NOT LIKE 'sqlite_%'
              AND name != 'schema_migrations'
            ORDER BY name
            """,
            (object_type,),
        )
    except DatabaseError as exc:
        raise SchemaInspectionError(
            f"Could not inspect SQLite {object_type}s: {exc}"
        ) from exc

    return [
        (
            str(_row_value(row, "name", 0)),
            str(_row_value(row, "sql", 1) or ""),
        )
        for row in rows
    ]


def _inspect_columns(
    database: Any,
    table_name: str,
) -> tuple[ColumnInfo, ...]:
    """Inspect columns belonging to a table."""
    escaped_table = table_name.replace(
        '"',
        '""',
    )

    try:
        rows = database.fetch_all(
            f'PRAGMA table_info("{escaped_table}")'
        )
    except DatabaseError as exc:
        raise SchemaInspectionError(
            f"Could not inspect columns for table "
            f"'{table_name}': {exc}"
        ) from exc

    columns = [
        ColumnInfo(
            name=str(_row_value(row, "name", 1)),
            data_type=str(
                _row_value(row, "type", 2) or ""
            ),
            not_null=bool(
                _row_value(row, "notnull", 3)
            ),
            default_value=(
                None
                if _row_value(row, "dflt_value", 4) is None
                else str(
                    _row_value(row, "dflt_value", 4)
                )
            ),
            primary_key_position=int(
                _row_value(row, "pk", 5)
            ),
        )
        for row in rows
    ]

    return tuple(
        sorted(
            columns,
            key=lambda column: (
                0
                if column.primary_key_position > 0
                else 1,
                column.primary_key_position
                if column.primary_key_position > 0
                else 0,
                column.name,
            ),
        )
    )


def _inspect_indexes(
    database: Any,
    table_name: str,
) -> tuple[IndexInfo, ...]:
    """Inspect indexes belonging to a table."""
    escaped_table = table_name.replace(
        '"',
        '""',
    )

    try:
        rows = database.fetch_all(
            f'PRAGMA index_list("{escaped_table}")'
        )
    except DatabaseError as exc:
        raise SchemaInspectionError(
            f"Could not inspect indexes for table "
            f"'{table_name}': {exc}"
        ) from exc

    indexes: list[IndexInfo] = []

    for row in rows:
        index_name = str(
            _row_value(row, "name", 1)
        )

        unique = bool(
            _row_value(row, "unique", 2)
        )

        escaped_index = index_name.replace(
            '"',
            '""',
        )

        try:
            column_rows = database.fetch_all(
                f'PRAGMA index_info("{escaped_index}")'
            )
        except DatabaseError as exc:
            raise SchemaInspectionError(
                f"Could not inspect index "
                f"'{index_name}': {exc}"
            ) from exc

        # PRAGMA index_info returns the columns in their actual
        # index sequence. That order is semantically significant
        # for composite indexes and must not be sorted.
        columns = tuple(
            str(
                _row_value(
                    column_row,
                    "name",
                    2,
                )
            )
            for column_row in column_rows
            if _row_value(
                column_row,
                "name",
                2,
            )
            is not None
        )

        indexes.append(
            IndexInfo(
                name=index_name,
                unique=unique,
                columns=columns,
            )
        )

    return tuple(
        sorted(
            indexes,
            key=lambda index: index.name,
        )
    )


def _inspect_foreign_keys(
    database: Any,
    table_name: str,
) -> tuple[ForeignKeyInfo, ...]:
    """Inspect foreign keys belonging to a table."""
    escaped_table = table_name.replace(
        '"',
        '""',
    )

    try:
        rows = database.fetch_all(
            f'PRAGMA foreign_key_list("{escaped_table}")'
        )
    except DatabaseError as exc:
        raise SchemaInspectionError(
            f"Could not inspect foreign keys for table "
            f"'{table_name}': {exc}"
        ) from exc

    foreign_keys = [
        ForeignKeyInfo(
            column=str(
                _row_value(row, "from", 3)
            ),
            referenced_table=str(
                _row_value(row, "table", 2)
            ),
            referenced_column=str(
                _row_value(row, "to", 4)
            ),
            on_update=str(
                _row_value(row, "on_update", 5)
            ),
            on_delete=str(
                _row_value(row, "on_delete", 6)
            ),
        )
        for row in rows
    ]

    return tuple(
        sorted(
            foreign_keys,
            key=lambda foreign_key: (
                foreign_key.column,
                foreign_key.referenced_table,
                foreign_key.referenced_column,
            ),
        )
    )


def inspect_schema(
    database: Database,
) -> DatabaseSchema:
    """Inspect the current SQLite database schema."""
    try:
        tables = _database_objects(
            database,
            "table",
        )

        views = _database_objects(
            database,
            "view",
        )

        table_infos = tuple(
            TableInfo(
                name=name,
                columns=_inspect_columns(
                    database,
                    name,
                ),
                indexes=_inspect_indexes(
                    database,
                    name,
                ),
                foreign_keys=_inspect_foreign_keys(
                    database,
                    name,
                ),
            )
            for name, _ in tables
        )

        view_infos = tuple(
            ViewInfo(
                name=name,
                sql=_normalize_sql(sql),
            )
            for name, sql in views
        )

        return DatabaseSchema(
            tables=tuple(
                sorted(
                    table_infos,
                    key=lambda table: table.name,
                )
            ),
            views=tuple(
                sorted(
                    view_infos,
                    key=lambda view: view.name,
                )
            ),
        )

    except SchemaInspectionError:
        raise
    except Exception as exc:
        raise SchemaInspectionError(
            f"Could not inspect database schema: {exc}"
        ) from exc


def schema_fingerprint(
    schema: DatabaseSchema,
) -> str:
    """Return the deterministic fingerprint of a schema."""
    return schema.fingerprint()


def inspect_and_fingerprint(
    database: Database,
) -> tuple[DatabaseSchema, str]:
    """Inspect a database and return its schema and fingerprint."""
    schema = inspect_schema(
        database
    )

    return (
        schema,
        schema_fingerprint(schema),
    )