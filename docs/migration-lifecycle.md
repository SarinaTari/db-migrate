# Migration Lifecycle

## Planned Lifecycle

A migration will eventually move through several stages:

```text
Created
  ↓
Discovered
  ↓
Parsed
  ↓
Validated
  ↓
Planned
  ↓
Executed
  ↓
Recorded
  ↓
Verified

Rollback follows a reverse path:

Recorded
  ↓
Selected for rollback
  ↓
Planned
  ↓
Executed using down SQL
  ↓
History updated
Current Lifecycle

At Phase 4, only the first part is implemented:

Migration File
      ↓
Discovery
      ↓
Parsing
      ↓
Validation
      ↓
Migration Object
Phase 5

Phase 5 will extend validation from individual files to the migration collection.

Phase 6+

Later phases will introduce:

database connections
execution
history
transactions
rollback
checksums
planning
schema verification