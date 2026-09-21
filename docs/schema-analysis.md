# Schema Analysis

## Overview

Schema analysis is one of the higher-level capabilities of `dbmigrate`.

The database migration system does not only track which migrations have been executed. It can also inspect database structure and analyze how schema changes affect that structure.

The schema-analysis subsystem supports:

- schema inspection
- schema representation
- schema comparison
- schema differences
- migration impact analysis
- schema fingerprints
- reproducibility analysis

The overall relationship is:

```text
Database
   │
   ▼
Schema Inspection
   │
   ▼
Schema Representation
   │
   ├───────────────┐
   ▼               ▼
Schema Diff    Fingerprint
   │               │
   ▼               ▼
Change Analysis  Integrity
```

---

# 1. Why Schema Analysis Exists

Migration history answers a question such as:

> Which migrations have been recorded as applied?

Schema analysis answers a different question:

> What does the database actually look like?

These are related but not identical.

For example:

```text
Migration History

001 applied
002 applied
003 applied
```

does not by itself prove that the database currently contains every object created by those migrations.

The schema subsystem provides a way to inspect the actual database structure.

---

# 2. Schema Inspection

Schema inspection reads structural information from the selected database.

Depending on the database backend, this can include:

```text
Tables
Columns
Column types
Nullability
Indexes
Constraints
```

The database-specific implementation performs the low-level inspection.

The result is converted into a common representation.

Conceptually:

```text
SQLite
PostgreSQL
MySQL
   │
   ▼
Database-specific inspection
   │
   ▼
Common schema representation
```

This allows the rest of the application to operate on schema information without depending directly on a particular database driver.

---

# 3. Common Schema Representation

A database schema can be represented as a structured collection of database objects.

Conceptually:

```text
Schema
├── Tables
│   ├── users
│   └── orders
│
├── Columns
│   ├── users.id
│   ├── users.name
│   └── orders.id
│
├── Indexes
│   └── users_name_idx
│
└── Constraints
```

The exact database representation differs between engines, but the analysis layer works with normalized information where possible.

---

# 4. Tables

Tables are one of the primary schema objects.

For example:

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);
```

The schema representation can describe:

```text
Table: users

Columns:
- id
- name
```

Multiple tables can then be compared between schemas.

---

# 5. Columns

Column information is important when determining whether two schemas are equivalent.

A column can have properties such as:

```text
Name
Type
Nullable
```

For example:

```text
users
├── id
│   ├── type: INTEGER
│   └── nullable: false
│
└── name
    ├── type: TEXT
    └── nullable: false
```

Column ordering is preserved where the underlying database exposes a defined order.

This matters for composite indexes and other schema structures whose meaning can depend on column order.

---

# 6. Indexes

Indexes are also part of the schema representation.

For example:

```sql
CREATE INDEX idx_users_email
ON users(email);
```

The schema can represent:

```text
Index: idx_users_email
Table: users
Columns:
- email
```

For composite indexes, the order of columns is significant.

For example:

```sql
CREATE INDEX idx_users_name_email
ON users(name, email);
```

is structurally different from:

```sql
CREATE INDEX idx_users_name_email
ON users(email, name);
```

The schema analysis system therefore preserves database-defined column ordering.

---

# 7. Schema Diff

Schema diff compares two schema representations and identifies structural differences.

Conceptually:

```text
Schema A
    │
    ├── users
    └── orders
         │
         ▼
      Compare
         ▲
         │
    ┌────┴────┐
    │         │
Schema B      │
    │         │
    ├── users │
    ├── orders│
    └── items │
```

The result can describe changes such as:

```text
Added table:
items
```

or:

```text
Removed column:
users.email
```

or:

```text
Changed column:
users.name
```

---

# 8. Schema Difference Categories

Schema differences can conceptually be grouped into:

```text
Added objects
Removed objects
Modified objects
```

For example:

```text
Added:
- products table
- users.email index

Removed:
- legacy_sessions table

Modified:
- users.name nullability
```

This makes structural changes easier to understand than comparing raw database metadata manually.

---

# 9. Schema Diff Is Not SQL Migration Generation

The schema-diff system identifies differences.

It does not mean that the tool automatically converts every difference into safe migration SQL.

For example:

```text
Schema A
users.name = TEXT

Schema B
users.name = VARCHAR(200)
```

The diff can report the change.

Automatically deciding how to safely transform existing production data is a separate problem.

The project intentionally does not attempt to provide a universal automatic schema-repair system.

---

# 10. Migration Impact Analysis

Migration impact analysis operates at the migration level.

For example:

```sql
CREATE TABLE users (...);
DROP TABLE legacy_users;
CREATE INDEX idx_users_email ON users(email);
```

The impact-analysis layer can identify operations such as:

```text
CREATE TABLE
DROP TABLE
CREATE INDEX
```

and classify their potential significance.

This allows developers to understand the possible effects of a migration before applying it.

---

# 11. Impact and Schema Analysis Are Different

The two systems operate at different levels.

### Migration Impact

Asks:

> What does this migration appear to do?

Example:

```text
DROP TABLE users
```

### Schema Diff

Asks:

> How are these two database schemas different?

Example:

```text
Schema A:
users exists

Schema B:
users does not exist
```

They complement each other:

```text
Migration
   │
   ▼
Impact Analysis
   │
   ▼
Expected Change
        │
        │
        ▼
Database Schema
        │
        ▼
Schema Diff
        │
        ▼
Observed Change
```

---

# 12. Schema Fingerprints

A schema fingerprint provides a compact representation of a schema.

Conceptually:

```text
Database Schema
      │
      ▼
Canonical Representation
      │
      ▼
Hash
      │
      ▼
Schema Fingerprint
```

A fingerprint can be used to compare schemas without manually comparing every object.

For example:

```text
Expected fingerprint:
abc123...

Actual fingerprint:
abc123...
```

indicates that the canonical representations match.

A different fingerprint indicates that the representations differ.

---

# 13. Canonicalization

Fingerprinting requires a deterministic representation.

If the same logical schema can be serialized in multiple arbitrary orders, hashing the raw representation could produce different fingerprints for equivalent schemas.

Therefore, schema information should be normalized into a deterministic representation before hashing.

Conceptually:

```text
Raw Schema
    │
    ▼
Normalize
    │
    ▼
Canonical Form
    │
    ▼
SHA-256
    │
    ▼
Fingerprint
```

The exact canonical representation is an implementation detail of the schema subsystem.

---

# 14. Fingerprints and Migration Integrity

Schema fingerprints provide another integrity signal.

For example:

```text
Migration History
       │
       ▼
Expected Schema
       │
       ▼
Expected Fingerprint
```

can be compared with:

```text
Actual Database
       │
       ▼
Actual Schema
       │
       ▼
Actual Fingerprint
```

Conceptually:

```text
Expected Fingerprint
        │
        ▼
      Compare
        ▲
        │
Actual Fingerprint
```

A mismatch indicates that the schemas represented by the fingerprints differ.

---

# 15. Reproducibility

Schema analysis is also useful for testing migration reproducibility.

The basic process is:

```text
Fresh Database
      │
      ▼
Apply Migration Chain
      │
      ▼
Inspect Schema
      │
      ▼
Generate Fingerprint
      │
      ▼
Compare
```

This tests whether the migration files are capable of creating the expected database structure from an empty starting point.

---

# 16. Why Fresh Database Testing Matters

A migration chain can work correctly on one existing database while still failing on a fresh database.

For example:

```text
Existing Database
    │
    ├── Historical manual changes
    ├── Migration changes
    └── Other state
```

may hide a problem in the migration chain.

A fresh database removes those historical side effects:

```text
Empty Database
      │
      ▼
Migration 001
      │
      ▼
Migration 002
      │
      ▼
Migration 003
      │
      ▼
Final Schema
```

This makes reproducibility testing a useful validation technique.

---

# 17. Current Reproducibility Scope

The current reproducibility implementation performs its fresh-database workflow with SQLite.

This provides a deterministic environment for testing migration chains.

The architecture, however, keeps schema inspection and database abstraction separate so that broader database-specific reproducibility support can be considered independently.

---

# 18. Schema Analysis Workflow

A typical schema-analysis workflow can be represented as:

```text
              ┌──────────────────┐
              │     Database     │
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ Schema Inspector │
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ Schema Structure │
              └────────┬─────────┘
                       │
          ┌────────────┼────────────┐
          │            │            │
          ▼            ▼            ▼
     Schema Diff   Fingerprint   Analysis
          │            │            │
          └────────────┼────────────┘
                       ▼
                Human-readable
                   results
```

---

# 19. Schema Analysis and the Migration Lifecycle

Schema analysis fits into the broader migration lifecycle.

Before execution:

```text
Migration
   │
   ├── Validate
   ├── Lint
   ├── Explain
   ├── Analyze Impact
   └── Plan
```

After execution:

```text
Database
   │
   ├── Inspect Schema
   ├── Compare Schema
   └── Verify Expected State
```

This creates a useful distinction:

```text
Before Migration
     │
     ▼
Expected Change

After Migration
     │
     ▼
Observed Change
```

The two can then be compared.

---

# 20. Schema Analysis Example

Suppose the initial database contains:

```text
users
├── id
└── name
```

A migration adds an email column:

```sql
ALTER TABLE users
ADD COLUMN email TEXT;
```

Before execution, impact analysis can identify:

```text
ALTER TABLE
ADD COLUMN
```

After execution, schema inspection can show:

```text
users
├── id
├── name
└── email
```

A schema comparison can then confirm that the expected structural change occurred.

---

# 21. Schema Analysis and Safety

Schema analysis can reveal potentially important changes before they are executed.

For example:

```text
Before:

users
orders
products
```

and a proposed migration that removes `products`.

The analysis can expose:

```text
Removed table:
products
```

This does not automatically reject the migration.

Instead, it makes the potential consequence explicit so that the migration can be reviewed.

---

# 22. Database Independence

Schema analysis operates above the individual database driver where possible.

The low-level database implementations handle engine-specific metadata queries.

The schema-analysis layer works with the resulting representation.

Conceptually:

```text
SQLite Metadata ───────┐
                       │
PostgreSQL Metadata ───┼──► Schema Representation
                       │
MySQL Metadata ────────┘
                              │
                              ▼
                       Schema Analysis
```

This separation allows the same analysis concepts to be reused across database engines.

---

# 23. Limitations

Schema analysis cannot perfectly understand every semantic property of every relational database.

Potential limitations include:

- database-specific metadata
- engine-specific constraints
- advanced SQL features
- stored procedures
- triggers
- generated objects
- vendor-specific types
- database extensions

The common schema representation intentionally focuses on the structural information exposed by the current implementation.

It should therefore not be interpreted as a complete universal model of every database feature.

---

# 24. Analysis vs. Repair

The project intentionally separates analysis from automatic repair.

For example:

```text
Detected Difference
       │
       ▼
Report Difference
```

rather than:

```text
Detected Difference
       │
       ▼
Automatically Modify Database
```

This is important because a schema difference does not necessarily indicate that the database should be changed.

The intended schema may need human investigation first.

---

# 25. Schema Analysis Design Goals

The schema-analysis subsystem aims to provide:

### Structural Visibility

Make the actual database schema inspectable.

### Deterministic Comparison

Represent schemas in a way that can be compared consistently.

### Migration Understanding

Connect migration operations with expected schema changes.

### Integrity Signals

Provide fingerprints and reproducibility checks.

### Database Portability

Keep higher-level analysis independent from database-driver details.

### Safe Diagnostics

Report differences without silently modifying the database.

---

# 26. Summary

Schema analysis extends `dbmigrate` beyond simple migration tracking.

The main components are:

```text
Schema Inspection
       │
       ▼
Schema Representation
       │
       ├── Schema Diff
       │
       ├── Impact Analysis
       │
       ├── Fingerprinting
       │
       └── Reproducibility
```

The central idea is to distinguish between:

```text
What the migration history says
```

and:

```text
What the database schema actually contains
```

By inspecting, comparing, and fingerprinting schemas, `dbmigrate` can provide additional evidence about database state and migration correctness without attempting to automatically repair unknown inconsistencies.