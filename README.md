# db-migrate

A Python-based database migration and schema-evolution CLI focused on safety, integrity, explainability, and migration analysis.

## Project Status

**Current phase: Phase 5 — Discovery and Validation**

Implemented:

- Professional Python project structure
- `dbmigrate` CLI
- Project configuration
- Project-root discovery
- Migration file format
- Migration parsing
- Migration discovery
- Deterministic migration ordering
- Duplicate migration-version detection
- Project-level migration validation
- Migration-gap detection
- Duplicate migration-name detection
- Structured validation reports
- `dbmigrate validate`
- Automated tests

Database execution has not been implemented yet.

SQLite will be introduced in Phase 6.

And the roadmap section should now show:

Phase 0   Database Migration Concepts             ✓
Phase 1   Professional Python Project             ✓
Phase 2   CLI Foundation                          ✓
Phase 3   Configuration                           ✓
Phase 4   Migration Format                        ✓
Phase 5   Discovery and Validation                ✓
Phase 6   Database Interface + SQLite             →
Phase 7   Migration History
Phase 8   Migration Runner
Phase 9   Transaction and Failure Semantics
Phase 10  Down / Rollback
Phase 11  Status / History / Current
Phase 12  Create Command
Phase 13  Validation
Phase 14  Checksums
Phase 15  Dry Run and Planning
Phase 16  Migration Linter
Phase 17  Explain and Impact
Phase 18  Schema Inspection / Fingerprints
Phase 19  Schema Diff / Reproducibility
Phase 20  Database Abstraction Review
Phase 21  PostgreSQL
Phase 22  MySQL
Phase 23  SQL Dialect / Capability System
Phase 24  Locking / Concurrency
Phase 25  Safety and Doctor
Phase 26  CI Mode
Phase 27  Logging
Phase 28  Performance
Phase 29  Full Integration Testing
Phase 30  Architecture Review
Phase 31  Documentation
Phase 32  Example Project
Phase 33  Portfolio Finalization