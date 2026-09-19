# Architecture

## 1. Purpose

This document defines the initial architectural direction for the database migration tool.

This is a **conceptual architecture**, not a final implementation.

The architecture is expected to evolve as real requirements appear.

---

# 2. High-Level Architecture

The planned system is:

```text
                    ┌───────────────┐
                    │      CLI      │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ Command Layer │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │   Migration   │
                    │    Service    │
                    └───────┬───────┘
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
          ▼                 ▼                 ▼
    ┌──────────┐      ┌──────────┐      ┌──────────┐
    │Discovery │      │ Planning │      │Validation│
    └──────────┘      └──────────┘      └──────────┘
          │                 │                 │
          └─────────────────┼─────────────────┘
                            ▼
                    ┌───────────────┐
                    │   Execution   │
                    └───────┬───────┘
                            │
                 ┌──────────┴──────────┐
                 ▼                     ▼
          ┌────────────┐        ┌────────────┐
          │  History   │        │ Integrity  │
          └────────────┘        └────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │   Database    │
                    │   Interface   │
                    └───────┬───────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
          ┌───────┐    ┌──────────┐   ┌───────┐
          │SQLite │    │PostgreSQL│   │ MySQL │
          └───────┘    └──────────┘   └───────┘
```

---

# 3. CLI Layer

The CLI is responsible for:

* parsing arguments
* selecting commands
* displaying results
* returning appropriate exit codes

It should not contain the migration engine itself.

For example:

```text
CLI
 │
 └── calls application/service layer
```

rather than:

```text
CLI
 │
 └── directly executes SQL everywhere
```

---

# 4. Migration Service

The migration service coordinates the migration workflow.

Conceptually:

```text
Migration Service
├── discover
├── validate
├── determine state
├── plan
├── execute
└── record history
```

It should coordinate these operations rather than implementing every database-specific detail itself.

---

# 5. Migration Discovery

Discovery is responsible for finding migration files.

Input:

```text
migrations/
```

Output:

```text
Migration objects
```

For example:

```text
001_create_users.sql
002_add_email.sql
003_create_projects.sql
```

becomes:

```text
[
    Migration(...),
    Migration(...),
    Migration(...)
]
```

---

# 6. Migration Representation

The system should have an internal representation of a migration.

Conceptually:

```text
Migration
├── version
├── name
├── path
├── up_sql
├── down_sql
└── checksum
```

This prevents the rest of the application from repeatedly parsing raw files.

---

# 7. Database Interface

The migration engine should interact with an abstraction rather than directly depending on one database implementation.

Conceptually:

```text
Database
    │
    ├── SQLiteDatabase
    ├── PostgreSQLDatabase
    └── MySQLDatabase
```

The exact interface will be determined when implementation begins.

---

# 8. Why an Interface?

Without an abstraction, the migration engine could become:

```python
if database == "sqlite":
    ...
elif database == "postgres":
    ...
elif database == "mysql":
    ...
```

repeated throughout the application.

That would make the code difficult to maintain.

Instead, the migration engine should ask for operations conceptually such as:

```text
connect
execute
begin
commit
rollback
query
close
```

while the adapter handles database-specific implementation.

---

# 9. Do Not Overabstract

The architecture should not create abstractions merely because they sound sophisticated.

For example, if there is no real need for:

```text
AbstractDatabaseFactoryProvider
```

then it should not exist.

The rule is:

> Introduce an abstraction when it solves a real problem.

---

# 10. Migration History

Migration history is responsible for answering:

```text
Which migrations have been applied?
```

It will eventually use a database table similar to:

```sql
schema_migrations
```

The history component should be separate from filesystem migration discovery.

---

# 11. Integrity

Integrity functionality will eventually handle:

```text
migration checksums
schema fingerprints
consistency verification
```

This allows the tool to detect mismatches between:

```text
migration source
```

and:

```text
database state
```

---

# 12. Analysis Layer

Later features will analyze migrations without executing them.

Conceptually:

```text
Migration
    │
    ├── Linter
    ├── Explainer
    └── Impact Analyzer
```

These components should not silently modify the database.

---

# 13. Schema Layer

Later the system will inspect actual database schemas.

Conceptually:

```text
Database
    │
    ▼
Schema Inspector
    │
    ├── Schema representation
    ├── Schema diff
    └── Schema fingerprint
```

This will support reproducibility and drift detection.

---

# 14. Doctor

The doctor command will eventually coordinate diagnostics from multiple components:

```text
Doctor
├── configuration
├── migration files
├── ordering
├── database connection
├── history
├── checksums
└── schema
```

The doctor should primarily diagnose.

It should not automatically modify a user's database without an explicit operation.

---

# 15. Dependency Direction

The desired dependency direction is approximately:

```text
CLI
 ↓
Application / Services
 ↓
Domain / Migration Models
 ↓
Database Abstraction
 ↓
Database Adapter
```

The lower-level components should not depend on the CLI.

For example:

```text
SQLite adapter
```

should not know whether it was called from:

```bash
dbmigrate up
```

or:

```bash
dbmigrate doctor
```

---

# 16. Architecture Evolution

This architecture is intentionally not frozen.

As implementation progresses, we will ask:

```text
Does this abstraction solve a real problem?

Does this module have one clear responsibility?

Is database-specific behavior isolated?

Is the CLI becoming too complicated?

Can this component be tested independently?
```

The architecture should be refined based on actual implementation experience.

---

# 17. Phase 0 Decision

At the end of Phase 0:

```text
No migration execution engine exists.
```

The architecture and domain model are defined conceptually.

Implementation begins in Phase 1.
