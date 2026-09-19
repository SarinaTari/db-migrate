## Migration lifecycle

The migration lifecycle is divided into distinct stages:

```text
Migration file
      |
      v
Parse
      |
      v
Discover
      |
      v
Validate
      |
      v
Plan
      |
      v
Execute
      |
      v
Record history

Phase 7 introduces the final Record history infrastructure.

The actual execution step is introduced in Phase 8.

A migration should only be recorded as applied after its SQL has successfully executed.

Similarly, a migration should only be removed from history after a successful rollback.

This separation prevents migration history from becoming an independent source of truth disconnected from database execution.