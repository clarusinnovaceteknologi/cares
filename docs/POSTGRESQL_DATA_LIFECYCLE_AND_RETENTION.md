# CARES PostgreSQL Data Lifecycle and Retention Design (Round 2)

**Status:** Proposed design documentation only; **NOT IMPLEMENTED, NOT TESTED**. This document evaluates partitioning, retention, archival, deletion, backup/recovery, and maintenance considerations for the proposed physical schema. No production capacity/performance claims are made. Confirmed requirements are separated from assumptions/proposed strategies.

## 1. Confirmed requirements vs assumptions

| Item | Classification | Basis / notes |
|---|---|---|
| PostgreSQL is primary system of record; modular monolith | Confirmed architectural constraint | Project architecture/ADRs. |
| Tenant isolation, auditable history, and evidence integrity required | Confirmed requirement intent | Security/data architecture and Round 1 design. |
| Original forensic evidence must not be silently rewritten or deleted; legal hold prevents unauthorized disposal | Confirmed design intent | Security architecture/evidence model. |
| Canonical asset IDs never reused; terminal/tombstoned history preserved | Confirmed design intent | Identity/licensing invariants, Round 1.1. |
| No exactly-once external delivery; unknown outcomes retained/reconciled | Confirmed design intent | Outbox/transaction semantics. |
| Specific retention durations, legal-hold workflows, purge SLAs, storage tiers, and RPO/RTO targets | **Assumption / open** | Require owner/legal/operational/security approval and workload validation (OD-010, OD-012). |
| Growth rates, partition thresholds, and maintenance windows | **Assumption / open** | Not measured; workload validation required. |

## 2. Partitioning evaluation

| Candidate table/group | Characteristics | Partitioning recommendation (proposed) | Rationale | Trade-offs / prerequisites |
|---|---|---|---|---|
| `ingest.event_receipt` | High-volume, append-heavy, time-based access, dedup uniqueness critical | **Candidate for RANGE partitioning by `received_at` (or event time) in future**; defer initial physical partitioning until volume/query patterns validated | Improves manageability, retention purge/archival by partition, and index locality for large histories | Requires careful uniqueness/index strategy across partitions (PostgreSQL partitioned unique constraints must include partition key), claim/query patterns, and migration planning. |
| `ingest.security_event` | High-volume, time-based queries, correlated to receipts | **Candidate for RANGE partitioning by `event_time`/`ingested_at`**; defer | Supports time-window SOC/investigation queries and retention management | Same global/partitioned uniqueness and FK considerations; join patterns with receipts must be validated. |
| `audit_evidence.audit_event` | Append-oriented, compliance/investigation retention, time-based access | **Candidate for RANGE partitioning by `occurred_at`**; defer | Large audit histories benefit from partition maintenance/retention operations | Must preserve immutability/integrity and efficient tenant/time/entity lookups; legal hold/retention rules may prevent simple drops. |
| `audit_evidence.forensic_evidence_record` / custody / versions / authorizations | Lower volume but strict legal-hold/integrity controls | **Generally not partitioned initially** (Proposed) | Complexity outweighs benefit; access is case/evidence-centric | Consider only with proven scale; partitioning must not complicate legal hold. |
| `processing.outbox_message` / `outbox_attempt` | Queue/state churn, retry/cleanup, time-based terminal cleanup | **Optional partitioning or table hygiene strategy later**; defer | Terminal-state cleanup and bloat control are primary concerns | Claim/lease queries and uniqueness (dedupe keys, attempt numbers) must remain efficient; partitioning can complicate queue scans. |
| `soc.asset_inventory_observation` | Potentially high-volume time-series snapshots | **Candidate for time-based partitioning**; defer | Observation history can grow quickly | Uniqueness/dedupe semantics and query patterns must be defined. |
| Core identity/licensing tables (`core.asset`, binding, ledger, usage state) | Correctness-critical, moderate volume, key-based access | **Not partitioned initially** (Proposed) | Strong transactional integrity and contention-sensitive updates favor simpler structures | Revisit only with evidence; tenant-based partitioning would require major key/FK design validation. |

**Partitioning guardrails (proposed):** do not partition without measured need; ensure partition keys are included in required unique constraints/indexes; restrict direct child-table access; test query plans, maintenance operations, and RLS behavior on partitioned tables before adoption.

## 3. Retention, archival, and deletion classes

| Data class | Proposed retention posture | Legal hold / deletion constraints | Notes |
|---|---|---|---|
| Canonical identity/licensing records (`core.asset`, `asset_data_source`, lineage, ledger, license events, tombstones) | Long-lived/historical retention by default (Proposed) | No reuse of canonical IDs; deletion restricted; reconcile before purge | Licensing/audit correctness and traceability depend on history. |
| Ingestion receipts and normalized security events | Time-bounded retention with archival strategy (Proposed/open) | Subject to investigation/legal/compliance holds | Partition/archival helpful at scale; dedup correctness windows must be considered. |
| Audit events and AI interaction audit | Long retention (compliance-driven, duration open) | Immutable intent; legal hold/policy governs purge | Integrity protections required. |
| Forensic evidence metadata/object versions/custody/authorizations | Retain per legal/investigation policy; objects and metadata aligned | **Legal hold blocks unauthorized disposal**; original evidence never silently rewritten/deleted | Controlled transitions only; storage lifecycle coordinated with DB metadata. |
| Outbox messages/attempts and processing work items | Retain terminal records for bounded operational/reconciliation window, then archive/purge per policy (Proposed) | Keep unknown/unresolved outcomes until reconciled | Cleanup must not remove evidence needed for delivery ambiguity resolution. |
| Support grants/approvals and controlled authorizations | Long retention for audit | Immutable decision history preferred | Compliance-sensitive. |
| Tenant configuration and AI consent/policy references | Versioned historical retention (Proposed) | Effective-date/audit traceability required | Supports governance reconstruction. |
| SOC operational records (alerts/cases/findings/observations) | Policy-based retention tiers (Proposed/open) | Case-linked or legal-hold records restricted from purge | Volume and investigative value vary. |

## 4. Soft delete, lifecycle state, and tombstones

- Prefer **explicit lifecycle/status transitions** and append-only history records over destructive deletes for correctness- and audit-critical entities.
- `core.asset_tombstone` provides a distinct terminal representation without reusing `asset_id`; lifecycle events/license events/lineage preserve continuity.
- Evidence records use controlled status transitions and custody/version history; "delete" operations, if ever permitted, require authorization, legal-hold checks, auditable execution, and consistency with external object storage (no silent deletion).
- Soft-delete flags, where used, must be consistently enforced in queries, unique constraints (partial uniques as needed), RLS/application logic, and retention jobs to avoid resurrection or leakage risks.

## 5. Tenant offboarding and historical preservation

- Offboarding is a controlled, auditable process: disable access, revoke grants/sessions/configurations as applicable, settle/record licensing and data-handling obligations, and apply approved retention/legal-hold/archive actions.
- Cross-tenant isolation remains enforced throughout offboarding/export/archive operations.
- Historical audit/evidence/licensing records required for compliance, dispute, or legal purposes must be preserved per policy; irreversible purge requires explicit authorization and verification that no legal hold applies.

## 6. Backup, restore, and disaster recovery (proposed)

- **Backups/PITR:** regular physical/logical backup strategy and point-in-time recovery capability are required for a system-of-record database (specific RPO/RTO targets **open/assumption**). WAL archiving and restore procedures must be tested in non-production environments.
- **Integrity:** backup/restore validation should include schema objects, critical constraints/indexes, and representative tenant-isolation and audit/evidence integrity checks (tests not performed).
- **Replication/failover:** read replicas or HA topology may be introduced later based on measured needs; failover behavior must preserve transaction durability semantics and not weaken RLS/role controls.
- **Logical exports:** tenant data export/offboarding tooling, if implemented, must be authorized, scoped, auditable, and consistent with privacy/legal requirements.

## 7. PostgreSQL maintenance and operations

- **Autovacuum/VACUUM/ANALYZE:** tune for high-churn tables (receipts, events, outbox, audit, observations) to control bloat and planner statistics; monitor dead tuples, table/index bloat, and long-running transactions.
- **Index maintenance:** monitor unused/redundant indexes and bloat; create/drop indexes via controlled migrations with measured benefit.
- **Constraint/check overhead:** correctness constraints add write overhead but are required; validate hot-path impact before implementation.
- **Partition maintenance (if adopted):** scheduled creation/detachment/archival of partitions under controlled jobs and privileges; ensure no bypass of retention/legal-hold rules.
- **Monitoring/alerting (proposed):** replication lag, backup success, WAL/archive health, lock contention, deadlocks, autovacuum lag, connection saturation, and long `in_progress`/`timeout_unknown_commit`/`unknown` outbox states.

## 8. Limitations and open dependencies

- Retention periods, archival media, legal-hold process details, encryption/key management specifics, and exact RPO/RTO objectives are not defined here and require formal approval (OD-010 and related governance decisions).
- Partitioning and index efficacy are workload-dependent; all recommendations require validation with representative data volumes and query patterns (OD-012).
- No maintenance jobs, backup scripts, partition DDL, or lifecycle automation are implemented in this round.
