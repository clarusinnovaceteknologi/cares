# CARES PostgreSQL Physical Schema Round 2 Changelog

**Status:** Documentation/design changelog only; **NOT IMPLEMENTED, NOT TESTED**. This changelog records Round 2 physical schema design artifacts created from the published Round 1.1 logical baseline on branch `design/postgresql-round2-physical-schema`.

## 1. Baseline and scope

- **Source baseline:** `audit/postgresql-round1-1-publication` at commit `c433fe897d1922c9e154a19b5646c99c3ec6d73d` (Round 1.1 audited/corrected publication state).
- **Scope:** PostgreSQL physical schema design documentation only. No executable DDL, migrations, database objects, roles/grants, RLS policies, ORM models, application code, or deployment artifacts were created. No ADR statuses changed (**ADR 0006 remains Proposed**).

## 2. Documents created

| Document | Purpose |
|---|---|
| [POSTGRESQL_PHYSICAL_SCHEMA_DESIGN.md](./POSTGRESQL_PHYSICAL_SCHEMA_DESIGN.md) | Physical schema organization, conventions, key/identity strategy, constraints/integrity, complete logical-to-physical entity mapping, per-table/column specifications, JSONB justification, assumptions/limitations. |
| [POSTGRESQL_PHYSICAL_ERD.md](./POSTGRESQL_PHYSICAL_ERD.md) | Physical Mermaid ERDs by domain with schema/table naming, tenant/global distinctions, and traceability notes. |
| [POSTGRESQL_INDEX_STRATEGY.md](./POSTGRESQL_INDEX_STRATEGY.md) | Proposed index inventory covering identity/binding, event dedup, idempotency, audit/evidence, time-based, outbox, and dashboard patterns with rationale and trade-offs. |
| [POSTGRESQL_RLS_AND_TENANT_ISOLATION_DESIGN.md](./POSTGRESQL_RLS_AND_TENANT_ISOLATION_DESIGN.md) | Tenant/global classification, verified transaction-bound context propagation, conceptual RLS/role model, and additional enforcement beyond RLS. |
| [POSTGRESQL_PHYSICAL_TRANSACTION_DESIGN.md](./POSTGRESQL_PHYSICAL_TRANSACTION_DESIGN.md) | Mapping of all 13 logical transaction operations to physical tables, constraints/indexes, locking/concurrency intent, retries, and recovery semantics. |
| [POSTGRESQL_DATA_LIFECYCLE_AND_RETENTION.md](./POSTGRESQL_DATA_LIFECYCLE_AND_RETENTION.md) | Partitioning evaluation, retention/legal-hold/deletion classes, backup/PITR/maintenance considerations, and explicit assumptions/open dependencies. |
| [POSTGRESQL_PHYSICAL_SCHEMA_OPEN_DECISIONS.md](./POSTGRESQL_PHYSICAL_SCHEMA_OPEN_DECISIONS.md) | Carried-forward OD-001–OD-013 statuses and new physical-design decisions (PD-001–PD-012), all unresolved items kept Proposed/Deferred (no approvals). |
| [POSTGRESQL_PHYSICAL_SCHEMA_ROUND2_CHANGELOG.md](./POSTGRESQL_PHYSICAL_SCHEMA_ROUND2_CHANGELOG.md) | This changelog. |
| [POSTGRESQL_PHYSICAL_SCHEMA_ROUND2_FINAL_REVIEW.md](./POSTGRESQL_PHYSICAL_SCHEMA_ROUND2_FINAL_REVIEW.md) | Traceability, consistency/Mermaid validation summary, unresolved risks, limitations, and readiness recommendation. |

## 3. Key design translations and preserved semantics

- **Complete traceability:** all Round 1.1 logical catalogue entities are mapped to proposed physical tables or explicitly bounded representations (optional dependent `core.source_device_key` projection; optional/non-core `processing.processing_work_item`), with no logical entity omitted.
- **Preserved Round 1.1 corrections:** authoritative `core.asset_data_source` binding owning immutable `source_device_key_id` (OD-002 Proposed), idempotency ledger scope/hash/state semantics (OD-008 Proposed), explicit `ingest.event_receipt` dedup namespace/provenance (OD-013 Proposed/partial), typed `core.asset_lineage_link` merge/split references only, distinct entity responsibilities/naming.
- **Invariants preserved:** verified transaction-bound tenant context only (no client-supplied tenant authority, no user-settable GUC authorization), RLS defense-in-depth, one-device-one-licensed-asset, external AI SaaS only with explicit selection/no silent failover, at-least-once/outbox unknown-outcome handling with **no exactly-once external delivery** claims.

## 4. Export/publication artifacts

- Regenerated HTML export and rebuilt [dist/CARES_DOCUMENTATION_HTML.zip](/home/ubuntu/cares/dist/CARES_DOCUMENTATION_HTML.zip) to include Round 2 documents (see [copilot.txt](/home/ubuntu/cares/copilot.txt) and final review for validation results and hashes).
- [copilot.txt](/home/ubuntu/cares/copilot.txt) updated with actual Round 2 execution report.

## 5. Limitations

- Mermaid diagrams structurally authored but **visual rendering not verified** in this environment.
- All designs are proposed and require implementation review, security/architecture/legal/commercial approvals where noted, and workload/operability validation before implementation.
