"""Database capability definitions for dbmigrate."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DatabaseCapabilities:
    """Describe features supported by a database engine."""

    transactional_ddl: bool
    drop_column: bool
    schemas: bool
    advisory_locks: bool

    def supports(self, capability: str) -> bool:
        """Return whether a named capability is supported."""
        try:
            return bool(getattr(self, capability))
        except AttributeError as exc:
            raise ValueError(
                f"Unknown database capability: {capability}"
            ) from exc