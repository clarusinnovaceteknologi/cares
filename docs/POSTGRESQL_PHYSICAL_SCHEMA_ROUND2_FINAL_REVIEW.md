# CARES PostgreSQL Physical Schema Round 2 — Final Review

**Status:** Proposed design review only; **NOT IMPLEMENTED, NOT TESTED**. This review evaluates the Round 2 PostgreSQL physical schema design documentation against the published Round 1.1 audited logical baseline. It does not authorize implementation, database object creation, ADR/status changes, or roadmap changes. **ADR 0006 remains Proposed.**

**Branch:** `design/postgresql-round2-physical-schema` (created from `origin/audit/postgresql-round1-1-publication`, baseline commit `c433fe897d1922c9e154a19b5646c99c3ec6d73d`). **Remote publication status at time of writing this document:** not yet pushed/verified (see [copilot.txt](/home/ubuntu/cares/copilot.txt) for final execution and publication verification results).

## 1. Executive summary

Round 2 translates the Round 1.1 logical baseline into a comprehensive proposed physical schema design covering schema organization, complete logical-to-physical mapping, per-table/column specifications, key/constraint strategy, index strategy, RLS/tenant-isolation design, transaction-to-physical mapping for all 13 critical operations, data lifecycle/retention considerations, open decisions, changelog, and this final review.

**Overall assessment:** the Round 2 documentation is **substantially complete and traceable** for implementation-planning purposes, with preserved Round 1.1 invariants (authoritative binding ownership, idempotency contract shape, explicit event dedup namespace semantics, typed lineage, no exactly-once external delivery) and preserved architectural/security constraints. However, multiple required approvals and validations remain open (notably OD-001–OD-009/OD-011/OD-013 and ADR 0006 acceptance, plus operational/workload validation and several physical-design finalizations). No executable DDL/migrations/DB objects were produced.

**Recommended readiness classification:** **READY FOR ROUND 3 IMPLEMENTATION PLANNING WITH EXPLICITLY BOUNDED EXCLUSIONS** (see §10).

## 2. Documents actually inspected (baseline and Round 2)

### 2.1 Baseline documents (inspected in this round)

- [docs/POSTGRESQL_LOGICAL_DATA_MODEL.md](./POSTGRESQL_LOGICAL_DATA_MODEL.md)
- [docs/POSTGRESQL_LOGICAL_ERD.md](./POSTGRESQL_LOGICAL_ERD.md)
- [docs/POSTGRESQL_TRANSACTION_BOUNDARIES.md](./POSTGRESQL_TRANSACTION_BOUNDARIES.md)
- [docs/POSTGRESQL_SCHEMA_OPEN_DECISIONS.md](./POSTGRESQL_SCHEMA_OPEN_DECISIONS.md)
- [docs/POSTGRESQL_LOGICAL_MODEL_ROUND1_1_FINAL_AUDIT.md](./POSTGRESQL_LOGICAL_MODEL_ROUND1_1_FINAL_AUDIT.md)
- [docs/DATA_ARCHITECTURE.md](./DATA_ARCHITECTURE.md)
- [docs/SECURITY_ARCHITECTURE.md](./SECURITY_ARCHITECTURE.md)
- [docs/POSTGRESQL_TECHNICAL_DECISIONS.md](./POSTGRESQL_TECHNICAL_DECISIONS.md)
- [docs/adr/0003-device-identity-and-asset-licensing.md](./adr/0003-device-identity-and-asset-licensing.md)
- [docs/adr/0005-event-processing-and-broker-evolution.md](./adr/0005-event-processing-and-broker-evolution.md)
- [docs/adr/0006-atomic-per-tenant-asset-licensing.md](./adr/0006-atomic-per-tenant-asset-licensing.md)
- [docs/PROJECT_STATUS.md](./PROJECT_STATUS.md)
- Export/packaging conventions and audit artifacts (`dist/cares-documentation-html/`, `dist/CARES_DOCUMENTATION_HTML.zip`, `dist/cares-external-audit/`, `copilot.txt`)

### 2.2 Round 2 documents produced and reviewed

- [docs/POSTGRESQL_PHYSICAL_SCHEMA_DESIGN.md](./POSTGRESQL_PHYSICAL_SCHEMA_DESIGN.md)
- [docs/POSTGRESQL_PHYSICAL_ERD.md](./POSTGRESQL_PHYSICAL_ERD.md)
- [docs/POSTGRESQL_INDEX_STRATEGY.md](./POSTGRESQL_INDEX_STRATEGY.md)
- [docs/POSTGRESQL_RLS_AND_TENANT_ISOLATION_DESIGN.md](./POSTGRESQL_RLS_AND_TENANT_ISOLATION_DESIGN.md)
- [docs/POSTGRESQL_PHYSICAL_TRANSACTION_DESIGN.md](./POSTGRESQL_PHYSICAL_TRANSACTION_DESIGN.md)
- [docs/POSTGRESQL_DATA_LIFECYCLE_AND_RETENTION.md](./POSTGRESQL_DATA_LIFECYCLE_AND_RETENTION.md)
- [docs/POSTGRESQL_PHYSICAL_SCHEMA_OPEN_DECISIONS.md](./POSTGRESQL_PHYSICAL_SCHEMA_OPEN_DECISIONS.md)
- [docs/POSTGRESQL_PHYSICAL_SCHEMA_ROUND2_CHANGELOG.md](./POSTGRESQL_PHYSICAL_SCHEMA_ROUND2_CHANGELOG.md)
- [docs/POSTGRESQL_PHYSICAL_SCHEMA_ROUND2_FINAL_REVIEW.md](./POSTGRESQL_PHYSICAL_SCHEMA_ROUND2_FINAL_REVIEW.md) (this document)

## 3. Logical-to-physical traceability

| Check | Result | Evidence |
|---|---|---|
| Complete logical entity mapping present | **PASS** | [POSTGRESQL_PHYSICAL_SCHEMA_DESIGN.md](./POSTGRESQL_PHYSICAL_SCHEMA_DESIGN.md) §3.3 and §6 define proposed physical representations for all 50 expected logical entities inventoried from the Round 1.1 baseline; targeted validation found no missing entity names from the expected set. |
| ERD-simplified/omitted logical entities represented physically | **PASS** | Mapped entities include `external_identity_subject`, `role_permission`, `membership_role_assignment`, `support_access_approval`, `source_device_fingerprint_alias`, `asset_identity_claim`, `identity_resolution_case`, `asset_tombstone`, `processing_work_item`, `evidence_object_version`, `evidence_custody_event`, `evidence_transition_authorization`, `ai_usage_budget_accounting`, and related records; physical ERD includes traceability notes. |
| Explicit bounded representation exceptions documented | **PASS WITH LIMITATIONS** | `core.source_device_key` documented as optional dependent/non-authoritative 1:1 projection or binding-owned attributes only (OD-002 bounded); `processing.processing_work_item` documented optional/non-core and must not replace receipt/outbox truth. Final materialization choices remain proposed. |
| All 13 logical transaction operations mapped | **PASS** | [POSTGRESQL_PHYSICAL_TRANSACTION_DESIGN.md](./POSTGRESQL_PHYSICAL_TRANSACTION_DESIGN.md) defines Operations 1–13 with tables, constraints/indexes, transaction intent, locking/concurrency, and failure/retry/recovery notes. |
| Traceability of critical invariants | **PASS WITH LIMITATIONS** | Authoritative binding ownership, idempotency ledger scope/hash/state, event receipt namespace/fallback basis, typed lineage FKs/mutual exclusivity, and outbox unknown-outcome/no-exactly-once semantics are explicitly represented; final enforcement predicates/formulas depend on open decisions and implementation validation. |

## 4. Cross-document consistency findings

| Area | Result | Findings |
|---|---|---|
| Schema organization, ownership, naming, and conventions | **PASS** | Consistent schema namespaces, table naming, shared-column conventions, and role/ownership posture across schema, index, RLS, transaction, and lifecycle documents. |
| Key/identity strategy and integrity model | **PASS WITH LIMITATIONS** | UUID surrogate PKs, tenant-aware uniqueness, authoritative binding identity, immutable canonical asset identity, and alternate business/idempotency keys are consistently specified. Composite tenant-FK enforcement is stated as required design intent but exact compositions require implementation finalization (PD-003, residual risk noted). |
| Tenant isolation and RLS model | **PASS** | All relevant documents preserve verified transaction-bound tenant context, prohibit client-supplied tenant authority and user-settable PostgreSQL GUC authorization, and treat RLS as defense in depth with least-privilege roles and additional constraints. |
| Index coverage for required patterns | **PASS WITH LIMITATIONS** | [POSTGRESQL_INDEX_STRATEGY.md](./POSTGRESQL_INDEX_STRATEGY.md) covers identity/binding resolution, event dedup namespaces, idempotency ledger, audit/evidence retrieval, time-based/dashboard queries, and outbox claiming/recovery. Several predicates/partial indexes and JSONB/expression choices remain proposed and workload-dependent. |
| Transaction mapping consistency | **PASS WITH LIMITATIONS** | Operations align with referenced tables/constraints/indexes and Round 1.1 semantics (ledger/event-receipt separation, typed lineage, no exactly-once). Concurrency mechanisms (e.g. `SKIP LOCKED`, isolation level choices) and accounting formulas are proposed/conditional. |
| Lifecycle/retention consistency | **PASS WITH LIMITATIONS** | Partitioning, retention, legal hold, tombstones, backup/PITR, and maintenance guidance align with data sensitivity and append-only/immutable intents; specific durations, triggers, and operational targets remain open/assumed (OD-010/OD-012). |
| Open decisions and status handling | **PASS** | OD-001–OD-013 carried forward with preserved statuses/intent; PD-001–PD-012 added as Proposed/Deferred; no unresolved item marked Approved; ADR 0006 remains Proposed. |

## 5. Mermaid validation results

| Artifact | Structural validation | Visual rendering | Result | Notes |
|---|---|---|---|---|
| [POSTGRESQL_PHYSICAL_ERD.md](./POSTGRESQL_PHYSICAL_ERD.md) | Performed (source inspection) | **NOT VERIFIED** | **PASS WITH LIMITATIONS** | 4 Mermaid fenced blocks detected (domain ERDs 1–4). No Mermaid renderer CLI (`mmdc`/`npx`) verified in environment; structural review only, no rendered-image/layout validation. |

## 6. Open decision reassessment (Round 2 impact)

| Decision(s) | Readiness impact | Classification |
|---|---|---|
| OD-001, OD-003, OD-004 (licensing accounting/counter/reservation semantics; ADR 0006 Proposed) | Block final licensing accounting/enforcement correctness approval; do not block documenting physical structures and implementation-planning boundaries | **Blocks specific physical/behavioral finalization; bounded in Round 2** |
| OD-002 (binding authority approval) | Affects final sign-off of authoritative binding uniqueness/authority (design follows recommended model) | **Blocks specific finalization** |
| OD-005, OD-006, OD-007, OD-008, OD-009, OD-013 | Affect merge/split policy details, fingerprint protection/rotation/overlap, re-enrollment handling, formal idempotency contract approval, outbox claim/fencing/unknown-delivery mechanics, and connector dedup fallback/predicates | **Block specific physical/operational finalization; bounded where possible** |
| OD-010, OD-011, OD-012 | Affect retention/legal-hold durations/processes, AI governance enforcement details, and workload/partition/index validation | **Deferred / validation or governance-dependent** |
| PD-001–PD-012 | Physical implementation choices requiring review/measurement (UUID ordering, enum/check strategy, composite FK pattern, RLS FORCE/object details, claim mechanics, dedup predicates, JSONB indexing, partition triggers, hash representation, scope modeling) | **Proposed/Deferred; non-blocking to planning if bounded** |

No open decision status was changed to Approved.

## 7. Unresolved issues, risks, and limitations

1. **Composite tenant-FK completeness:** physical design requires tenant-consistent relationships, but exact composite FK/unique-key composition for all critical paths must be finalized and validated to eliminate cross-tenant reference risk beyond RLS. (**Risk: security/integrity**)
2. **Licensing accounting semantics unresolved:** committed/reserved/capacity formulas and timeout/reconciliation behaviors depend on OD-001/003/004 and ADR 0006 acceptance. (**Blocks specific finalization**)
3. **Binding/idempotency/dedup approvals pending:** OD-002/OD-008/OD-013 require formal approval and connector-specific finalization for predicates/fallbacks. (**Blocks specific finalization**)
4. **Outbox and unknown-outcome operations:** lease/fencing/claim mechanics and reconciliation procedures (OD-009) require implementation validation; no exactly-once external delivery is possible/claimed. (**Operational risk**)
5. **Fingerprint protection and evidence lifecycle governance:** key custody, hash/protection representation, overlap semantics, retention/legal-hold durations, and controlled disposal procedures remain open (OD-006/OD-010/PD-011). (**Security/compliance dependency**)
6. **Workload-dependent choices not validated:** indexing efficacy, partitioning thresholds, UUID choice impact, autovacuum tuning, query plans, and contention behavior are untested assumptions (OD-012). (**NOT VERIFIED**)
7. **Mermaid visual rendering:** not performed; only structural source inspection completed. (**NOT VERIFIED**)
8. **No implementation artifacts:** absence of DDL/migrations/roles/policies/tests means no runtime correctness, isolation, or performance can be claimed.

## 8. Evidence summary

- **Document existence:** all nine required Round 2 documents present under `docs/` (verified by file checks).
- **Entity coverage:** 50 expected logical entity names found in [POSTGRESQL_PHYSICAL_SCHEMA_DESIGN.md](./POSTGRESQL_PHYSICAL_SCHEMA_DESIGN.md) mapping/specification context (no missing names in targeted check).
- **Key semantics present:** authoritative binding ownership text, idempotency scope fields/index references (`tenant_id`, `operation_type`, `idempotency_key`), explicit `event_namespace`/dedup basis fields, and typed lineage fields (`merge_operation_id`, `split_operation_id`) with non-polymorphic design stated.
- **Transaction coverage:** Operations 1–13 headings present in [POSTGRESQL_PHYSICAL_TRANSACTION_DESIGN.md](./POSTGRESQL_PHYSICAL_TRANSACTION_DESIGN.md).
- **Mermaid structure:** 4 fenced Mermaid blocks in [POSTGRESQL_PHYSICAL_ERD.md](./POSTGRESQL_PHYSICAL_ERD.md).
- **Invariant preservation:** RLS/isolation document states tenant authority only from trusted, verified, transaction-bound context, never from client-supplied tenant IDs and never from user-settable PostgreSQL GUCs for authorization decisions.
- Export/package validation results, file hashes, and git publication verification are recorded in [copilot.txt](/home/ubuntu/cares/copilot.txt) upon completion of execution steps.

## 9. Scope and compliance statement

- This round produced **documentation/design artifacts only**. No PostgreSQL DDL, migrations, Alembic scripts, tables, indexes, constraints, triggers, functions, procedures, views, materialized views, sequences, roles, grants, RLS policies, extensions, ORM models, application code, or database deployment steps were created.
- Existing ADR statuses were not changed; **ADR 0006 remains Proposed**. Established roadmap and prior approved decisions were not reopened. Proposed/open decisions were not marked Approved.
- No claims of implementation, testing, rendering, performance, production readiness, or validation are made beyond checks explicitly performed and recorded.

## 10. Final readiness assessment

**Recommendation:** **READY FOR ROUND 3 IMPLEMENTATION PLANNING WITH EXPLICITLY BOUNDED EXCLUSIONS**

**Rationale:**
- The Round 2 physical design provides comprehensive, traceable, implementation-oriented documentation across all required domains (schema/entities, keys/constraints/integrity, indexing, RLS/isolation, transaction mapping, lifecycle/retention, open decisions) while preserving Round 1.1 semantics and project invariants.
- Implementation planning can proceed to define migration sequencing, detailed DDL/policy implementation approach, test/validation plans, and approval gates, provided the exclusions below are explicitly bounded and tracked.

**Explicitly bounded exclusions / conditions for Round 3 planning:**
- **Requires formal approval before implementation sign-off:** OD-001/003/004 (licensing accounting/counters/reservations, ADR 0006 context), OD-002 (binding authority), OD-005 (merge/split policy/effects), OD-006 (fingerprint protection/rotation/overlap), OD-007 (re-enrollment/reset), OD-008 (idempotency contract/coupling approval), OD-009 (outbox mechanics/unknown-delivery handling), OD-013 (connector dedup namespaces/fallback predicates), and relevant privacy/legal/security approvals for OD-010/OD-011.
- **Must be finalized/validated during implementation planning or pre-implementation:** composite tenant-FK patterns (PD-003), verified-context DB mechanism implementation details (PD-005, within invariant constraints), RLS FORCE/ownership specifics (PD-006), claim/lease mechanics (PD-007), dedup uniqueness predicates (PD-008), UUID/type/hash representation choices (PD-001/PD-002/PD-011), and scope modeling details (PD-012).
- **Requires workload/operability validation:** index effectiveness, partitioning triggers/keys, JSONB indexing needs, autovacuum/maintenance tuning, capacity/RPO-RTO targets, and query/concurrency behavior (OD-012, PD-009/PD-010).
- **Not verified in this round:** Mermaid visual rendering, runtime isolation/performance/correctness, and any unexecuted tests.

**Blocked issues (specific, not whole-round blockers):** none identified that prevent implementation planning as a documentation/planning activity; however, the approvals and validations above **block final implementation correctness/approval** for affected areas until resolved.

**Stop condition:** Round 2 documentation/design work is complete for this execution. **Do not start Round 3 implementation** and do not create SQL/migrations/application implementation without explicit project-owner authorization.
