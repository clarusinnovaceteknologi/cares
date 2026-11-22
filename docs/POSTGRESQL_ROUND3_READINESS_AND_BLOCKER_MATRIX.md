# CARES PostgreSQL Round 3 Readiness and Blocker Matrix

**Status:** Proposed planning assessment only; **NOT IMPLEMENTED, NOT TESTED, NOT APPROVED FOR EXECUTION**. This matrix classifies readiness for future implementation increments based on the Round 2 baseline and recorded open decisions. It does not authorize implementation and does not resolve OD/PD/ADR items.

**Related documents:** [POSTGRESQL_ROUND3_IMPLEMENTATION_PLAN.md](./POSTGRESQL_ROUND3_IMPLEMENTATION_PLAN.md), [POSTGRESQL_ROUND3_IMPLEMENTATION_WORK_BREAKDOWN.md](./POSTGRESQL_ROUND3_IMPLEMENTATION_WORK_BREAKDOWN.md), [POSTGRESQL_ROUND3_MIGRATION_AND_DEPLOYMENT_STRATEGY.md](./POSTGRESQL_ROUND3_MIGRATION_AND_DEPLOYMENT_STRATEGY.md), [POSTGRESQL_ROUND3_TEST_AND_ACCEPTANCE_PLAN.md](./POSTGRESQL_ROUND3_TEST_AND_ACCEPTANCE_PLAN.md), [POSTGRESQL_ROUND3_DEPENDENCY_MAP.md](./POSTGRESQL_ROUND3_DEPENDENCY_MAP.md), [POSTGRESQL_ROUND3_FINAL_REVIEW.md](./POSTGRESQL_ROUND3_FINAL_REVIEW.md), [POSTGRESQL_PHYSICAL_SCHEMA_OPEN_DECISIONS.md](./POSTGRESQL_PHYSICAL_SCHEMA_OPEN_DECISIONS.md), [POSTGRESQL_SCHEMA_OPEN_DECISIONS.md](./POSTGRESQL_SCHEMA_OPEN_DECISIONS.md), [POSTGRESQL_PHYSICAL_SCHEMA_ROUND2_FINAL_REVIEW.md](./POSTGRESQL_PHYSICAL_SCHEMA_ROUND2_FINAL_REVIEW.md).

## 1. Readiness classification definitions

| Classification | Meaning in this matrix |
|---|---|
| **Ready** | Planning is coherent and no known technical ambiguity blocks a future explicitly authorized, bounded, non-production increment for the stated scope, subject to preconditions and validation gates. (No such runtime-exposed tenant increment is claimed here.) |
| **Conditionally ready** | Can be prepared/implemented in a bounded future increment only after specified approvals, validations, mechanism decisions, or evidence are satisfied. |
| **Blocked** | Cannot be safely implemented without owner/security/legal/commercial/operational decisions or required validations; proceeding would risk violating unresolved invariants. |
| **Deferred** | Intentionally postponed pending evidence, thresholds, or governance inputs; not required for an initial bounded structural increment but required for later operational maturity as applicable. |

## 2. Component/increment readiness matrix

| Component / increment | Scope summary | Readiness | Depends on | Blocking OD/PD/ADR/issues | Required approvals / evidence before execution | Notes |
|---|---|---|---|---|---|---|
| I-00 Authorization & environment readiness | Scope control, environment/tooling/process readiness | Conditionally ready | Round 2 baseline, owner intent | None formal, but prerequisites unresolved | Owner authorization, DBA/ops/security preflight, migration/change-control process | Mandatory gate for any future implementation. |
| I-01 Schema namespaces & conventions | Schemas, naming, type/state conventions | Conditionally ready | I-00 | PD-001, PD-002, PD-004 | Engineering/DBA decisions; PostgreSQL version/feature confirmation | Do not assume final UUID/state representation without decision. |
| I-02 Global/catalog foundations | `core.tenant`, `core.external_identity_subject`, `core.role`, `core.role_permission`, `ingest.event_schema_reference`, `soc.threat_intelligence_reference` | Conditionally ready | I-01 | PD-012 (scope-sensitive elements) | Design review, access-posture review | Low tenant-runtime coupling but still requires controlled rollout. |
| I-03 Tenant access/config structures | Membership, role assignments, support access, tenant configuration | Conditionally ready | I-02 | PD-003 | Tenant-consistent FK/composite-key strategy approval | Must support audited, time-bound support access model. |
| I-04 Canonical asset & authoritative binding | `core.asset`, `integration_ai.data_source`, `core.asset_data_source`, optional `core.source_device_key`, aliases, claims | Conditionally ready | I-03 | OD-002, OD-006, OD-007, PD-004, PD-011 | OD-002 bounded approval, fingerprint/protection/key-rotation policy inputs, security review | Authoritative binding and immutable `source_device_key_id` must be preserved. |
| I-05 Identity lifecycle/lineage/tombstones | Resolution, lifecycle, merge/split ops, typed lineage, tombstones | Conditionally ready | I-04 | OD-005, OD-007 | Authorization/evidence policy inputs for merge/split; typed integrity validation | No polymorphic lineage; no canonical ID reuse. |
| I-06 Licensing/entitlement/ledger structures | Entitlement, usage state, license events/reservations, identity idempotency ledger | **Blocked (final semantics)** / conditionally ready for bounded structural planning only | I-04, I-05 | OD-001, OD-003, OD-004, OD-008, PD-001/002/003; ADR 0006 Proposed | Formal approvals of accounting, reservation, coupling/contract semantics; DBA/security review | **Must not implement/claim finalized quota/accounting behavior without approvals.** |
| I-07 Ingestion/event structures | `event_receipt`, `security_event` | Conditionally ready | I-02, I-04 | OD-013, PD-008 | Connector namespace/fallback approval or explicit bounded connector scope; dedup predicate validation | Event dedup must remain distinct from identity/licensing ledger. |
| I-08 Outbox/processing structures | Outbox messages/attempts, optional work items | Conditionally ready | I-07 | OD-009, PD-007 | Lease/fencing/retry/unknown-outcome semantics approval; claim mechanism validation plan | No exactly-once external delivery. |
| I-09 Audit/evidence & AI governance | `audit_evidence.*`, integration/AI config/consent/secret-ref/budget/audit | Conditionally ready | I-03, I-04, I-08 | OD-010, OD-011, PD-011 | Legal/privacy/security/compliance approvals; controlled-transition/object-storage sequencing design | Legal hold and evidence integrity are release-sensitive. |
| I-10 SOC operational structures | Alerts, cases, detection rules/versions, findings, TI refs, inventory observations | Conditionally ready | I-02, I-04, I-07 | OD-010, OD-012, PD-009, PD-012 | Scope/access governance, retention assumptions, query/index validation plan | Global-vs-tenant rule scope must not create leakage paths. |
| I-11 Integrity/index hardening (non-partitioning subset) | Tenant-consistent FKs/uniques/CHECKs, selected indexes | Conditionally ready | I-02–I-10 | PD-003, PD-008, PD-009, OD-012 | DB/security review, workload/query-plan validation | Avoid unvalidated GIN/index proliferation. |
| I-12 Verified context, roles/privileges, RLS | Transaction-bound verified context, least-privilege roles, RLS policies/FORCE posture | **Blocked** | I-11 | PD-005, PD-006, OD-010 (controlled admin implications) | Security/DBA/architecture approval, hardened mechanism review, pooling/reset and negative isolation test evidence | **No client-supplied tenant IDs; no user-settable PostgreSQL GUC authorization.** |
| I-13 Transactional/runtime semantics implementation | Operations 1–13 behavior, ledger/outbox runtime, evidence transitions | **Blocked / out of Round 3 scope** | I-12 and domain increments | OD-001,003,004,005,008,009,010,011,013 and relevant PDs | Full prerequisite approvals, validated designs, authorized implementation plan | Not authorized/executable in this planning round. |
| I-14 Partitioning/maintenance/retention automation | Partition adoption, purge/archive/legal-hold automation, tuning | **Deferred / Blocked by evidence & governance** | I-11, operational evidence | OD-010, OD-012, PD-010 | Measured thresholds, legal/compliance/ops approvals, runbooks | Do not adopt prematurely. |

## 3. Open decision and dependency blockers (summary)

| ID | Status (preserved) | Blocks / constrains | Owner/approval type |
|---|---|---|---|
| OD-001 | Proposed / pending ADR acceptance (ADR 0006 Proposed) | Licensing accounting/enforcement semantics finalization (I-06, I-13) | Architecture/security/ADR governance, commercial as applicable |
| OD-002 | Proposed (open approval) | Authoritative binding/uniqueness/finality for identity structures (I-04+) | Architecture/data-model/security |
| OD-003 | Proposed (open approval) | Reservation/timeout/committed-reserved semantics (I-06, Ops 1/9) | Product/commercial/security/ops |
| OD-004 | Proposed (open approval) | Tenant-level counter scope/reconciliation formulas (I-06) | Commercial/product/finance as applicable |
| OD-005 | Proposed (open approval) | Merge/split authorization/evidence/licensing effects (I-05, Ops 6/7) | Security/governance/product/compliance |
| OD-006 | Proposed (open approval) | Fingerprint protection, custody, rotation overlap (I-04, Ops 3/4) | Security/cryptography/platform ops |
| OD-007 | Proposed (open approval) | Reinstall/re-enrollment/reset lifecycle rules (I-04/I-05) | Architecture/product/operations |
| OD-008 | Proposed (open approval) | Idempotency contract, states, coupling, reconciliation (I-06, Ops 1–9) | Technical architecture/data consistency |
| OD-009 | Proposed (open approval) | Outbox leasing/fencing/retry/unknown-delivery handling (I-08, Ops 11/12) | Engineering/reliability/operations |
| OD-010 | Deferred / pending governance approval | Retention/legal hold/deletion/archive classes and automation (I-09/I-14, evidence lifecycle) | Legal/compliance/privacy/security |
| OD-011 | Deferred / pending policy and privacy approval | AI consent/classification/redaction/budget/provider governance (I-09) | Product/privacy/legal/security/commercial |
| OD-012 | Deferred / validation required | Workload/index/partition/capacity validation (I-11/I-14, performance planning) | DBA/operations/engineering |
| OD-013 | Proposed (open/partial) | Connector event identity namespace/fallback dedup predicates (I-07, Op 10) | Architecture/integration/operations/security |
| PD-001–PD-012 | Proposed/Deferred as recorded | Physical mechanism choices, index/partition/FK/RLS/context/claim/hash/scope strategies | Engineering/DBA/security/architecture as applicable |
| ADR 0006 | Proposed (unchanged) | Formal acceptance of licensing invariants and schema-level implications | ADR governance/architecture/security owners |

## 4. Overall Round 3 planning readiness statement

- **Implementation planning artifacts:** complete in this round if all required Round 3 documents are produced, cross-referenced, and published with validated exports.
- **Bounded implementation execution:** **not ready without explicit owner authorization and prerequisite approvals/validations**. Tenant-scoped/runtime implementation is **blocked** by verified-context/RLS approval and validation (PD-005/PD-006) and by unresolved semantic/governance dependencies (notably OD-001/002/003/004/005/008/009/010/011/013 where applicable).
- **Safe first increment:** only a tightly bounded, authorized, non-production structural/preparatory increment may be considered after I-00 prerequisites; it cannot claim tenant-safe runtime readiness or resolved licensing/idempotency semantics.
