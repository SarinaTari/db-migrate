# Phase 0 — Understanding Database Migrations

## Objective

Understand the problem domain before implementing the migration engine.

The goal is not to write a large amount of code.

The goal is to understand exactly what the software will be responsible for.

---

# 1. Learning Objectives

By the end of Phase 0, I should understand:

* database schemas
* schema evolution
* migrations
* migration versions
* migration ordering
* migration history
* up migrations
* down migrations
* transactions
* commit
* rollback
* ACID
* DDL
* DML
* migration integrity
* checksums
* schema drift
* reproducibility
* migration planning
* migration analysis

---

# 2. Core Mental Model

A database starts at some schema state:

```text
Schema 0
```

Then migrations transform it:

```text
Schema 0
   │
   │ 001
   ▼
Schema 1
   │
   │ 002
   ▼
Schema 2
   │
   │ 003
   ▼
Schema 3
```

The migration system records this sequence.

---

# 3. Important Distinction

The project manages:

```text
Schema evolution
```

not simply:

```text
SQL files
```

A migration is meaningful because it represents a versioned change to the database state.

---

# 4. Migration State

The tool eventually needs to compare:

```text
Migrations available in repository
```

against:

```text
Migrations recorded in database
```

For example:

```text
Repository:

001
002
003
004
005

Database:

001
002
003
```

Therefore:

```text
Current = 003

Pending:

004
005
```

---

# 5. Migration Lifecycle

The lifecycle is:

```text
Create
 ↓
Write
 ↓
Discover
 ↓
Parse
 ↓
Validate
 ↓
Plan
 ↓
Execute
 ↓
Record
 ↓
Verify
```

Each stage has a separate responsibility.

---

# 6. Why Planning Matters

The tool should eventually support:

```bash
dbmigrate plan
```

which might produce:

```text
Current version: 003

Pending:

004_add_projects
005_add_tasks
006_add_indexes

No changes have been made.
```

This allows the developer to inspect what would happen before execution.

---

# 7. Why Integrity Matters

Suppose:

```text
002_add_email.sql
```

was applied.

Its checksum was:

```text
abc123
```

Later the file changes.

The current checksum becomes:

```text
def456
```

The migration engine should detect:

```text
Applied migration has been modified.
```

The historical migration should not silently change.

---

# 8. Why Reproducibility Matters

Given:

```text
Empty database
```

and:

```text
001
002
003
004
005
```

the tool should eventually be able to construct:

```text
Expected current schema
```

This allows the project to verify that its migration history actually represents the schema it claims to represent.

---

# 9. Why Multiple Database Engines Matter

The project will eventually support:

```text
SQLite
PostgreSQL
MySQL
```

However, these engines differ.

Differences can involve:

* SQL syntax
* data types
* schema metadata
* DDL behavior
* transaction behavior
* locking
* indexes
* constraints

Therefore:

```text
One migration engine
+
database-specific adapters
```

is the intended architecture.

---

# 10. Safety Philosophy

The tool should prefer:

```text
Show
→ Explain
→ Validate
→ Plan
→ Execute
```

rather than:

```text
Execute immediately
```

Potentially destructive operations should be visible.

The tool should not make unjustified claims that an operation is universally safe or unsafe.

---

# 11. Distinctive Features

The project will eventually add:

```text
Migration Planner
Migration Linter
Explain Mode
Impact Analysis
Schema Inspection
Schema Diff
Schema Fingerprints
Migration Doctor
Reproducibility Verification
CI Mode
Migration Locking
```

These features will come after the core engine.

---

# 12. Scope Boundary

The project will not attempt to become:

```text
ORM
Database backup tool
Cloud database manager
Universal SQL translator
Distributed database orchestrator
Full Alembic replacement
Full Flyway replacement
Full Liquibase replacement
```

The focus remains:

```text
Migration
+
Schema evolution
+
Integrity
+
Analysis
+
Developer tooling
```

---

# 13. Phase 0 Completion Criteria

Phase 0 is complete when I can answer these questions without memorizing definitions:

### Question 1

What problem does a migration solve?

### Question 2

Why should migrations be versioned?

### Question 3

How does the tool determine which migrations are pending?

### Question 4

Why should an applied migration normally be immutable?

### Question 5

Why are transactions important during migration execution?

### Question 6

What is the difference between DDL and DML?

### Question 7

Why can't we assume SQLite, PostgreSQL, and MySQL behave identically?

### Question 8

Why is a migration history table necessary?

### Question 9

What is schema drift?

### Question 10

Why is reproducibility important?

### Question 11

Why should planning be separated from execution?

### Question 12

Why should an SQL analyzer distinguish detected facts from assumptions?

---

# 14. Implementation Boundary

No migration execution code is required in Phase 0.

The implementation begins in:

```text
Phase 1 — Professional Python Project Foundation
```

Phase 0 establishes the conceptual foundation on which that implementation will be built.
