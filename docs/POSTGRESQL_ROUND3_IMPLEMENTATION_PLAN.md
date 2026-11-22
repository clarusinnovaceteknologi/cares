# CARES PostgreSQL Round 3 Implementation Plan

**Status:** Proposed implementation-planning document only; **NOT IMPLEMENTED, NOT TESTED, NOT APPROVED FOR EXECUTION**. This document translates the Round 2 physical schema design into a bounded, sequenced implementation plan. It does **not** create DDL, migration files, ORM models, database roles/policies, triggers/functions/procedures, database objects, or application/database implementation. No design element is claimed as implemented, tested, operational, production-ready, or authorized for execution.

**Round 3 scope:** planning, sequencing, dependency mapping, readiness/blocker assessment, migration/deployment strategy, and test/acceptance planning only.

## 1. Authoritative baseline and inspected sources

### 1.1 Repository and baseline
- **Repository:** `https://github.com/clarusinnovaceteknologi/cares`
- **Planning branch:** `planning/postgresql-round3-implementation`
- **Verified baseline commit (Round 2 synchronized):** `ea1eb79372a1fa04a2cdc4a87b2117fa3c23b20d`
- **Round 2 original artifact commit (historical evidence):** `ea7ca9adf226ab7b321a6f89d0e1ab520794a4d8`
- **Round 1.1 publication baseline:** `c433fe897d1922c9e154a19b5646c99c3ec6d73d`

### 1.2 Inspected baseline documents (planning inputs)
Round 1.1 logical baseline: [POSTGRESQL_LOGICAL_DATA_MODEL.md](./POSTGRESQL_LOGICAL_DATA_MODEL.md), [POSTGRESQL_LOGICAL_ERD.md](./POSTGRESQL_LOGICAL_ERD.md), [POSTGRESQL_TRANSACTION_BOUNDARIES.md](./POSTGRESQL_TRANSACTION_BOUNDARIES.md), [POSTGRESQL_SCHEMA_OPEN_DECISIONS.md](./POSTGRESQL_SCHEMA_OPEN_DECISIONS.md), [POSTGRESQL_LOGICAL_MODEL_ROUND1_1_CHANGELOG.md](./POSTGRESQL_LOGICAL_MODEL_ROUND1_1_CHANGELOG.md), [POSTGRESQL_LOGICAL_MODEL_ROUND1_1_FINAL_AUDIT.md](./POSTGRESQL_LOGICAL_MODEL_ROUND1_1_FINAL_AUDIT.md).

Round 2 physical baseline: [POSTGRESQL_PHYSICAL_SCHEMA_DESIGN.md](./POSTGRESQL_PHYSICAL_SCHEMA_DESIGN.md), [POSTGRESQL_PHYSICAL_ERD.md](./POSTGRESQL_PHYSICAL_ERD.md), [POSTGRESQL_INDEX_STRATEGY.md](./POSTGRESQL_INDEX_STRATEGY.md), [POSTGRESQL_RLS_AND_TENANT_ISOLATION_DESIGN.md](./POSTGRESQL_RLS_AND_TENANT_ISOLATION_DESIGN.md), [POSTGRESQL_PHYSICAL_TRANSACTION_DESIGN.md](./POSTGRESQL_PHYSICAL_TRANSACTION_DESIGN.md), [POSTGRESQL_DATA_LIFECYCLE_AND_RETENTION.md](./POSTGRESQL_DATA_LIFECYCLE_AND_RETENTION.md), [POSTGRESQL_PHYSICAL_SCHEMA_OPEN_DECISIONS.md](./POSTGRESQL_PHYSICAL_SCHEMA_OPEN_DECISIONS.md), [POSTGRESQL_PHYSICAL_SCHEMA_ROUND2_CHANGELOG.md](./POSTGRESQL_PHYSICAL_SCHEMA_ROUND2_CHANGELOG.md), [POSTGRESQL_PHYSICAL_SCHEMA_ROUND2_FINAL_REVIEW.md](./POSTGRESQL_PHYSICAL_SCHEMA_ROUND2_FINAL_REVIEW.md).

Architecture/security/project/ADR baselines: [ARCHITECTURE.md](./ARCHITECTURE.md), [SECURITY_ARCHITECTURE.md](./SECURITY_ARCHITECTURE.md), [DATA_ARCHITECTURE.md](./DATA_ARCHITECTURE.md), [THREAT_MODEL.md](./THREAT_MODEL.md), [TECHNOLOGY_SELECTION.md](./TECHNOLOGY_SELECTION.md), [DEVELOPMENT_ROADMAP.md](./DEVELOPMENT_ROADMAP.md), [REQUIREMENTS_TRACEABILITY.md](./REQUIREMENTS_TRACEABILITY.md), [PROJECT_STATUS.md](./PROJECT_STATUS.md), and ADRs [0001](./adr/0001-modular-monolith.md)–[0006](./adr/0006-atomic-per-tenant-asset-licensing.md) (**ADR 0006 remains Proposed**).

## 2. Non-negotiable invariants (must be preserved by every future increment)

| Invariant | Planning implication |
|---|---|
| PostgreSQL is the primary system of record; modular monolith; core remains functional without MELIRA | Schema/migration planning must prioritize relational correctness and core domains before optional AI-dependent behavior. |
| MELIRA is external SaaS only (explicit provider/model/region), no silent failover, no automatic transfer, no local inference, no local GPU | No local AI inference/GPU infrastructure in DB or migration planning; AI tables/config remain governance/audit references only. |
| One unique monitored device = one licensed asset per tenant; equal device-type licensing weight; multi-source same-device does not create duplicate licensing | Identity binding, ledger, usage-state, merge/split, and idempotency increments must preserve atomic per-tenant accounting semantics and cannot be implemented as assumed-final where OD/PD dependencies remain open. |
| Strict tenant isolation: tenant authority only from trusted, verified, transaction-bound context; never client-supplied tenant IDs; never user-settable PostgreSQL GUC authorization | Any runtime-capable increment touching tenant data requires approved/verified context mechanism and RLS/privilege validation before exposure; RLS is defense-in-depth, not sufficient alone. |
| `core.asset_data_source` authoritative stable binding owning immutable `source_device_key_id`; aliases resolve to same binding (OD-002 Proposed) | Physical implementation must not create competing identity authority or mutable stable binding keys. |
| Identity/licensing idempotency ledger scope `(tenant_id, operation_type, idempotency_key)` with deterministic canonical hash/state semantics (OD-008 Proposed); event dedup explicit namespace/provenance in `ingest.event_receipt` (OD-013 Proposed), distinct from identity ledger | Ledger and receipt semantics must remain separated; no reuse of one for the other. |
| Typed lineage only (`from_asset_id`, `to_asset_id`, `merge_operation_id` or `split_operation_id`); no polymorphic lineage refs | Constraints/transaction logic must enforce typed lineage integrity. |
| No exactly-once external delivery; unknown outcomes retained/reconciled | Outbox/worker planning must preserve at-least-once, idempotent handling, and unknown-outcome visibility. |
| OD-001–OD-013 and PD-001–PD-012 remain as recorded; ADR statuses unchanged | Planning may prepare bounded work but must not silently approve/close/implement disputed semantics. |

## 3. Sequencing principles

1. **Dependency-first, invariant-first:** foundational schemas/types/catalogs and integrity primitives before dependent tables, before RLS/policy hardening, before operational indexes/partitioning optimizations, before application/runtime exposure.
2. **Separate structural correctness from runtime authorization:** schema/constraint correctness can be planned as bounded non-production increments only where it does not violate unresolved invariants or imply tenant-safe runtime access; tenant-scoped runtime behavior remains gated by verified context/RLS validation.
3. **Atomicity boundaries preserved:** migration units and future transaction implementations must align with Round 2 operation boundaries (Operations 1–13) and must not split correctness-critical coupled state changes.
4. **No destructive/ambiguous shortcuts:** no implicit tenant authority, no weakening of uniqueness/tenant consistency, no exactly-once claims, no auto-resolution of open decisions.
5. **Validation gates before promotion:** each increment requires explicit preconditions, verification evidence, rollback/recovery planning, and owner/security/operational approval where applicable.
6. **Bounded exclusions explicit:** unresolved OD/PD items, unvalidated performance/retention assumptions, and unapproved security mechanisms remain exclusions/blockers, not assumptions.

## 4. Proposed implementation phases and increments

> **Readiness legend:** **Ready (bounded planning target)** = planning/preparation coherent and not blocked by technical ambiguity for a future explicitly authorized, non-production structural increment, subject to stated preconditions; **Conditionally ready** = can proceed only after specific approvals/validations/evidence; **Blocked** = cannot be safely implemented without owner decision, security approval, or required validation.

| Phase | Increment | Objective | Primary dependencies (Round 2 refs) | Readiness | Key approvals/evidence |
|---|---|---|---|---|---|
| P0 | I-00 Planning authorization and environment readiness | Confirm owner authorization scope, target PostgreSQL environment class, migration tooling/process, backup/restore discipline, and change-control boundaries for future implementation | Round 2 final review, lifecycle/maintenance assumptions, PD-001/002/003 decisions where relevant | Conditionally ready | Owner authorization, environment/DBA/security readiness evidence |
| P1 | I-01 Schema namespaces, extensions-as-needed planning, and shared type/domain conventions | Establish `core`, `ingest`, `processing`, `audit_evidence`, `integration_ai`, `soc`, and conditional `security_internal` organization and agreed type/state conventions | Physical schema §3; PD-001, PD-002, PD-004 | Conditionally ready | Engineering/DBA convention approval; UUID/state representation decision (PD-001/002) |
| P1 | I-02 Platform/global/catalog foundations | Foundational/global tables with minimal dependencies: `core.tenant`, `core.external_identity_subject`, `core.role`, `core.role_permission`, `ingest.event_schema_reference`, `soc.threat_intelligence_reference` (as modeled) | Physical schema §6.1, 6.3, 6.7; RLS global/catalog posture | Conditionally ready | Review of scope/global access model (PD-012 where applicable) |
| P1 | I-03 Core tenant-access and configuration structures | `core.tenant_membership`, `core.membership_role_assignment`, `core.support_access_grant`, `core.support_access_approval`, `core.tenant_configuration` with tenant-consistent constraints | I-02, Physical schema §6.1, tenant-consistency strategy PD-003 | Conditionally ready | Tenant-consistent FK/composite-key pattern approval (PD-003) |
| P2 | I-04 Asset/integration authoritative binding foundations | `core.asset`, `integration_ai.data_source`, `core.asset_data_source` (authoritative), optional dependent `core.source_device_key` (if PD-004 materialized), `core.source_device_fingerprint_alias`, `core.asset_identity_claim` | I-02/I-03, Physical schema §6.2/6.6, OD-002/006/007 | Conditionally ready | OD-002 approval/bounded acceptance; PD-004/PD-011 decisions; fingerprint protection assumptions reviewed |
| P2 | I-05 Identity lifecycle, lineage, and tombstone structures | `core.identity_resolution_case`, `core.asset_lifecycle_event`, `core.asset_merge_operation`, `core.asset_split_operation`, `core.asset_lineage_link` (typed), `core.asset_tombstone` | I-04, Transaction Ops 3–8, lineage integrity rules | Conditionally ready | OD-005/007 policy approvals for operational semantics; typed lineage constraints validated in design |
| P2 | I-06 Licensing/entitlement/ledger structures | `core.subscription_entitlement`, `core.tenant_license_usage_state`, `core.asset_license_event`, `core.identity_operation_idempotency_ledger`, `core.asset_license_reservation` | I-04/I-05, Transaction Ops 1/2/6/7/8/9, OD-001/003/004/008 | **Blocked for final semantics / conditionally ready for bounded structural planning only** | OD-001/003/004/008 approvals; PD-001/002/003; accounting formulas not to be finalized without approval |
| P3 | I-07 Ingestion and event structures | `ingest.event_receipt`, `ingest.security_event`, tenant-scoped integration/SOC observation dependencies as needed | I-02/I-04, Transaction Op 10, OD-013, PD-008 | Conditionally ready | OD-013 connector namespace/fallback approval or explicit bounded scope; dedup uniqueness predicate decisions |
| P3 | I-08 Processing/outbox structures | `processing.outbox_message`, `processing.outbox_attempt`, optional `processing.processing_work_item` | I-07 and domain producers as applicable, Transaction Ops 11/12, OD-009, PD-007 | Conditionally ready | OD-009 lease/fencing/reconciliation semantics; PD-007 claim mechanism validation plan |
| P3 | I-09 Audit/evidence and AI governance structures | `audit_evidence.*` tables and `integration_ai.*` governance/accounting tables, AI interaction audit correlation | I-02–I-08 correlations, Transaction Op 13, OD-010/011, lifecycle/legal-hold constraints | Conditionally ready | OD-010/011 governance/legal/privacy approvals; evidence storage/object sequencing procedures defined |
| P3 | I-10 SOC operational structures | `soc.alert`, `soc.incident_case`, `soc.detection_rule`, `soc.detection_rule_version`, `soc.vulnerability_finding`, `soc.asset_inventory_observation` | I-02/I-04/I-07, PD-012 scope modeling | Conditionally ready | Detection-rule scope/access governance (PD-012), retention assumptions (OD-010/012) |
| P4 | I-11 Integrity hardening: tenant-consistent FKs, CHECKs, partial/unique indexes, and contention-sensitive indexes | Apply/refine constraints and index set per Round 2 design/index strategy (excluding unapproved/invalid assumptions) | Prior structural increments, index strategy, PD-003/008/009 | Conditionally ready | DB design/security review, workload/index validation plan (OD-012), measured trade-off acceptance |
| P5 | I-12 Verified tenant context, roles/privileges, and RLS rollout (defense-in-depth) | Implement approved verified transaction-bound context mechanism, least-privilege roles, grants, and RLS policies/force posture per approved design | I-01–I-11, RLS design, PD-005/006 | **Blocked pending security/DBA approval and validation** | PD-005/006 approval, hardened helper review, pooling/reset design, negative/isolation test evidence; no GUC/client tenant authority |
| P5 | I-13 Transactional behavior, idempotency/outbox runtime semantics, and controlled procedures | Implement operation-aligned transactional logic/procedures/worker behavior only as separately authorized future work | I-12 and all relevant domain structures, Transaction Ops 1–13, OD-008/009 | **Blocked / not in scope of Round 3 execution** | Owner authorization, approved semantics, security and correctness validation, non-production then controlled promotion |
| P6 | I-14 Partitioning/maintenance/retention automation (deferred optimization/operations) | Adopt partitioning or lifecycle automation only after measured thresholds and approved retention/legal-hold rules | Lifecycle design, OD-010/012, PD-010, validated workload | **Blocked/Deferred** | Legal/compliance/operations approvals, workload evidence, runbook and rollback validation |

## 5. Increment detail template (applies to every future implementation increment)

For each authorized increment, the implementation owner must document and satisfy:
- **Objective and in-scope objects/operations** (tables, constraints, indexes, policies, or behaviors; explicit exclusions).
- **Preconditions and entry criteria** (prior increments complete, approvals obtained, environment ready, backups/change window if applicable).
- **Dependencies** (schema/object, OD/PD/ADR, tooling, security mechanism, data/governance).
- **Risks and invariant checks** (tenant isolation, binding authority, idempotency separation, typed lineage, no exactly-once claims, licensing semantics).
- **Rollback/recovery approach** (forward-fix vs rollback migration strategy, backup/PITR considerations, irreversibility assessment).
- **Verification evidence required** (schema/object inspection, constraint/index checks, negative security tests, transaction/idempotency tests, migration dry-run/rehearsal evidence as applicable).
- **Owner approvals required** (architecture, security/DBA, product/commercial, legal/compliance/privacy, operations).

## 6. Smallest safe first implementation increment (candidate, bounded)

**Candidate:** **I-00 (planning authorization/environment readiness)** followed by a **bounded I-01/I-02 structural preparation increment in a non-production, isolated environment only** (schema namespace and selected global/catalog foundation objects with reviewed naming/type conventions), executed only under explicit owner authorization and strict change control.

**Why this is the smallest coherent candidate:** it has the fewest domain invariants coupled to unresolved tenant-runtime authorization and licensing-accounting semantics, while establishing traceable structural prerequisites.

**Mandatory caveats:**
- Not authorized by this plan; requires explicit owner authorization and environment/DBA controls.
- Must not include tenant-runtime RLS/policy claims, user-settable GUC context, client-supplied tenant authority, licensing enforcement semantics, or any behavior that violates unresolved OD/PD-gated invariants.
- Any object touching tenant-owned semantics beyond isolated structural validation requires prior resolution/approval of relevant dependencies (especially PD-005/006 for runtime isolation, OD-001/002/003/004/008 for identity/licensing correctness).
- **Cannot begin safely as tenant-scoped/runtime implementation without violating unresolved invariants and missing approvals.**

## 7. Explicit out of scope (Round 3 planning and unauthorized execution)

- PostgreSQL DDL, migration files, ORM models, DB roles/policies/grants, triggers/functions/procedures, partition DDL, or database provisioning/modification/execution.
- Application repositories/services, runtime code, or integration implementation.
- Changes to Round 1.1/Round 2 schema definitions, OD/PD statuses, ADR statuses, architecture, or roadmap.
- Visual rendering verification of Mermaid diagrams (structural validation only when export is performed).
- Production/capacity/performance/RPO/RTO claims or test-pass claims without executed evidence.

## 8. Related Round 3 documents

- [POSTGRESQL_ROUND3_IMPLEMENTATION_WORK_BREAKDOWN.md](./POSTGRESQL_ROUND3_IMPLEMENTATION_WORK_BREAKDOWN.md)
- [POSTGRESQL_ROUND3_MIGRATION_AND_DEPLOYMENT_STRATEGY.md](./POSTGRESQL_ROUND3_MIGRATION_AND_DEPLOYMENT_STRATEGY.md)
- [POSTGRESQL_ROUND3_TEST_AND_ACCEPTANCE_PLAN.md](./POSTGRESQL_ROUND3_TEST_AND_ACCEPTANCE_PLAN.md)
- [POSTGRESQL_ROUND3_READINESS_AND_BLOCKER_MATRIX.md](./POSTGRESQL_ROUND3_READINESS_AND_BLOCKER_MATRIX.md)
- [POSTGRESQL_ROUND3_DEPENDENCY_MAP.md](./POSTGRESQL_ROUND3_DEPENDENCY_MAP.md)
- [POSTGRESQL_ROUND3_CHANGELOG.md](./POSTGRESQL_ROUND3_CHANGELOG.md)
- [POSTGRESQL_ROUND3_FINAL_REVIEW.md](./POSTGRESQL_ROUND3_FINAL_REVIEW.md)
