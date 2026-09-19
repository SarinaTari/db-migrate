# Migration Lifecycle

## Overview

The migration lifecycle describes how a migration moves from an idea to an applied database change.

The planned lifecycle is:

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

---

## 1. Create

The developer creates a migration:

```bash
dbmigrate create add_email
```

This will eventually generate something similar to:

```text
002_add_email.sql
```

---

## 2. Write

The developer defines the database changes.

Example:

```sql
-- +up

ALTER TABLE users
ADD COLUMN email TEXT;

-- +down

ALTER TABLE users
DROP COLUMN email;
```

The migration becomes part of the project's version-controlled source.

---

## 3. Discover

The migration engine scans:

```text
migrations/
```

and finds migration files.

For example:

```text
001_create_users.sql
002_add_email.sql
003_create_projects.sql
```

---

## 4. Parse

Each migration file is converted into an internal representation.

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

The migration engine should not repeatedly interpret raw filenames and text throughout the application.

---

## 5. Validate

The system checks things such as:

```text
duplicate versions
invalid filenames
missing sections
empty migrations
invalid ordering
malformed migration metadata
```

Later validation may include:

```text
checksum verification
SQL analysis
database compatibility checks
```

---

## 6. Determine Current State

The database contains migration history.

For example:

```text
001
002
003
```

The repository contains:

```text
001
002
003
004
005
```

Therefore:

```text
Current:
003

Pending:
004
005
```

---

## 7. Plan

The migration engine determines exactly what would happen.

Example:

```text
Migration Plan

Current version:
003

Target version:
005

Pending migrations:

004_add_tasks
005_add_indexes
```

No database modification occurs during planning.

---

## 8. Execute

When the user chooses to apply the plan:

```text
004
  ↓
005
```

The migration engine executes the SQL in the appropriate order.

---

## 9. Transaction

Where supported and appropriate:

```text
BEGIN
   ↓
Migration SQL
   ↓
Record migration history
   ↓
COMMIT
```

If execution fails:

```text
BEGIN
   ↓
Migration SQL
   ↓
ERROR
   ↓
ROLLBACK
```

The exact semantics depend on the database and operations involved.

---

## 10. Record

After successful application, the migration history is updated.

Conceptually:

```text
version
name
checksum
applied_at
```

This allows future executions to determine that the migration has already been applied.

---

## 11. Verify

After execution, the system can eventually verify:

```text
Migration history
        vs
Expected schema
```

and later:

```text
Expected schema
        vs
Actual schema
```

This forms the basis of schema-drift detection.

---

## 12. Complete Lifecycle

The final conceptual pipeline is:

```text
                ┌─────────────┐
                │    Create   │
                └──────┬──────┘
                       ▼
                ┌─────────────┐
                │    Write    │
                └──────┬──────┘
                       ▼
                ┌─────────────┐
                │   Discover  │
                └──────┬──────┘
                       ▼
                ┌─────────────┐
                │    Parse    │
                └──────┬──────┘
                       ▼
                ┌─────────────┐
                │   Validate  │
                └──────┬──────┘
                       ▼
                ┌─────────────┐
                │    Plan     │
                └──────┬──────┘
                       ▼
                ┌─────────────┐
                │   Execute   │
                └──────┬──────┘
                       ▼
                ┌─────────────┐
                │    Record   │
                └──────┬──────┘
                       ▼
                ┌─────────────┐
                │   Verify    │
                └─────────────┘
```

---

## Important Principle

The migration engine should keep these stages conceptually separate.

For example:

```text
Planning
```

should not silently modify the database.

Likewise:

```text
Validation
```

should not silently repair migrations.

And:

```text
Analysis
```

should not silently execute SQL.

Each stage should have a clear responsibility.
