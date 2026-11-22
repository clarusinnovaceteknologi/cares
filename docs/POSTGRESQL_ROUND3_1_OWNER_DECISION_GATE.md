# CARES PostgreSQL Round 3.1 — Owner Decision & Authorization Gate

**Status:** Proposed governance and decision-preparation document only; **NOT IMPLEMENTED, NOT TESTED, NOT APPROVED FOR EXECUTION, NOT AN IMPLEMENTATION AUTHORIZATION**. This document prepares an auditable owner decision and authorization gate based on the completed Round 3 implementation-planning baseline. It does **not** make owner decisions, does **not** authorize implementation, and does **not** resolve open decisions.

**Source baseline (verified):** branch `planning/postgresql-round3-implementation`, commit `ee6e005bc50ffa8f3cd376a83b01369044005c3b` (independently verified as remote HEAD before this Round 3.1 branch was created). **Target branch:** `governance/postgresql-round3-owner-decision-gate` (created from the exact verified source commit in an isolated worktree). The original Round 3 planning branch remains unchanged by this task.

## 1. Purpose and boundaries

### 1.1 Purpose
This Round 3.1 package enables the project owner to:
1. Understand which decisions remain unresolved (OD-001–OD-013, PD-001–PD-012, and related governance/approval dependencies).
2. Understand why each decision matters, including technical, security, operational, compliance, and commercial consequences where source-backed.
3. Review viable alternatives and implications as supported by source documents, with Copilot analysis clearly distinguished from source-backed material.
4. Distinguish decisions that block specific implementation increments from conditional prerequisites and deferrable decisions.
5. Record explicit owner decisions and, separately, explicit owner authorization for narrowly defined implementation increments using provided templates.
6. Preserve all existing architectural constraints, exclusions, and unresolved statuses.

### 1.2 Boundaries (governance only)
- **In scope:** traceable decision/register/brief/authorization-matrix/template/dependency-map/final-review documentation derived from actual repository sources.
- **Out of scope:** implementation, schema execution, runtime behavior changes, approval of decisions, promotion of ADR status, closure of OD/PD items, and any assumption that planning readiness or publication of this package authorizes development.
- **No fabrication:** no owner decision, date, signature, approval, or authorization record is created or implied.

## 2. Authoritative sources inspected (repository truth)

Inspected from the verified source commit (non-exhaustive list of primary inputs):
- Round 3 planning: [POSTGRESQL_ROUND3_IMPLEMENTATION_PLAN.md](./POSTGRESQL_ROUND3_IMPLEMENTATION_PLAN.md), [POSTGRESQL_ROUND3_IMPLEMENTATION_WORK_BREAKDOWN.md](./POSTGRESQL_ROUND3_IMPLEMENTATION_WORK_BREAKDOWN.md), [POSTGRESQL_ROUND3_MIGRATION_AND_DEPLOYMENT_STRATEGY.md](./POSTGRESQL_ROUND3_MIGRATION_AND_DEPLOYMENT_STRATEGY.md), [POSTGRESQL_ROUND3_TEST_AND_ACCEPTANCE_PLAN.md](./POSTGRESQL_ROUND3_TEST_AND_ACCEPTANCE_PLAN.md), [POSTGRESQL_ROUND3_READINESS_AND_BLOCKER_MATRIX.md](./POSTGRESQL_ROUND3_READINESS_AND_BLOCKER_MATRIX.md), [POSTGRESQL_ROUND3_DEPENDENCY_MAP.md](./POSTGRESQL_ROUND3_DEPENDENCY_MAP.md), [POSTGRESQL_ROUND3_CHANGELOG.md](./POSTGRESQL_ROUND3_CHANGELOG.md), [POSTGRESQL_ROUND3_FINAL_REVIEW.md](./POSTGRESQL_ROUND3_FINAL_REVIEW.md), [POSTGRESQL_ROUND3_PUBLICATION_AUDIT.md](./POSTGRESQL_ROUND3_PUBLICATION_AUDIT.md).
- Round 2: [POSTGRESQL_PHYSICAL_SCHEMA_ROUND2_FINAL_REVIEW.md](./POSTGRESQL_PHYSICAL_SCHEMA_ROUND2_FINAL_REVIEW.md), [POSTGRESQL_PHYSICAL_SCHEMA_OPEN_DECISIONS.md](./POSTGRESQL_PHYSICAL_SCHEMA_OPEN_DECISIONS.md), [POSTGRESQL_PHYSICAL_SCHEMA_DESIGN.md](./POSTGRESQL_PHYSICAL_SCHEMA_DESIGN.md), [POSTGRESQL_PHYSICAL_TRANSACTION_DESIGN.md](./POSTGRESQL_PHYSICAL_TRANSACTION_DESIGN.md), [POSTGRESQL_RLS_AND_TENANT_ISOLATION_DESIGN.md](./POSTGRESQL_RLS_AND_TENANT_ISOLATION_DESIGN.md), [POSTGRESQL_INDEX_STRATEGY.md](./POSTGRESQL_INDEX_STRATEGY.md), [POSTGRESQL_DATA_LIFECYCLE_AND_RETENTION.md](./POSTGRESQL_DATA_LIFECYCLE_AND_RETENTION.md).
- Round 1.1/logical: [POSTGRESQL_LOGICAL_DATA_MODEL.md](./POSTGRESQL_LOGICAL_DATA_MODEL.md), [POSTGRESQL_LOGICAL_MODEL_ROUND1_1_FINAL_AUDIT.md](./POSTGRESQL_LOGICAL_MODEL_ROUND1_1_FINAL_AUDIT.md).
- Architecture/security/project/ADR: [ARCHITECTURE.md](./ARCHITECTURE.md), [SECURITY_ARCHITECTURE.md](./SECURITY_ARCHITECTURE.md), [THREAT_MODEL.md](./THREAT_MODEL.md), [DATA_ARCHITECTURE.md](./DATA_ARCHITECTURE.md), [DEVELOPMENT_ROADMAP.md](./DEVELOPMENT_ROADMAP.md), [REQUIREMENTS_TRACEABILITY.md](./REQUIREMENTS_TRACEABILITY.md), [PROJECT_STATUS.md](./PROJECT_STATUS.md).

**Source availability/gap notes (factual):**
- [POSTGRESQL_SCHEMA_OPEN_DECISIONS.md](./POSTGRESQL_SCHEMA_OPEN_DECISIONS.md) (Round 1/1.1 logical open-decision register) is **not present as a committed file at the verified source commit** (`ee6e005`), although it is referenced by some baseline documents (e.g. Round 1.1 final audit and physical open decisions). OD-001–OD-013 are therefore traced from committed sources that carry them forward (notably [POSTGRESQL_PHYSICAL_SCHEMA_OPEN_DECISIONS.md](./POSTGRESQL_PHYSICAL_SCHEMA_OPEN_DECISIONS.md), [POSTGRESQL_ROUND3_READINESS_AND_BLOCKER_MATRIX.md](./POSTGRESQL_ROUND3_READINESS_AND_BLOCKER_MATRIX.md), [POSTGRESQL_ROUND3_IMPLEMENTATION_PLAN.md](./POSTGRESQL_ROUND3_IMPLEMENTATION_PLAN.md), [POSTGRESQL_ROUND3_FINAL_REVIEW.md](./POSTGRESQL_ROUND3_FINAL_REVIEW.md), and Round 1.1/Round 2 review/audit records) and marked where original-register detail is unavailable.
- A committed ADR markdown source for ADR 0006 (e.g. `docs/adr/0006-atomic-per-tenant-asset-licensing.md`) is **not present at the verified source commit**; repository source documents consistently state **ADR 0006 remains Proposed**. This status is preserved and not promoted.

## 3. Current Round 3 readiness position (preserved baseline)

From [POSTGRESQL_ROUND3_FINAL_REVIEW.md](./POSTGRESQL_ROUND3_FINAL_REVIEW.md) and [POSTGRESQL_ROUND3_READINESS_AND_BLOCKER_MATRIX.md](./POSTGRESQL_ROUND3_READINESS_AND_BLOCKER_MATRIX.md):
- Round 3 implementation-planning artifacts are coherent and published, but **safe progression to tenant-scoped/runtime or correctness-critical implementation is blocked** by unresolved/required approvals and validations.
- **No component is unconditionally ready for runtime/production implementation.**
- **Conditionally ready (planning/bounded structural preparation, not authorization):** I-00, I-01, I-02, I-03, I-04, I-05, I-07, I-08, I-09, I-10, and selected I-11 hardening activities, subject to stated approvals/validations/preconditions.
- **Blocked / blocked final semantics / out of scope:** I-06 final semantics (OD-001/003/004/008, ADR 0006 Proposed); I-12 (PD-005/PD-006 verified tenant context/RLS and required validation); I-13 (blocked/out of Round 3 scope pending prerequisites and authorization); I-14 (deferred/blocked by evidence and governance).
- **Final Round 3 planning status:** `BLOCKED BY OWNER DECISIONS` (planning complete; implementation not authorized).

## 4. Planning readiness, owner decision, implementation authorization, and implementation completion (distinguished)

| Concept | Meaning | What it does **not** mean |
|---|---|---|
| **Planning readiness** | Design/planning artifacts are sufficiently coherent and traceable to support bounded, governed next steps subject to preconditions. | Does not authorize implementation, execution, deployment, or exposure of runtime behavior. |
| **Owner decision** | An explicit, recorded selection/deferral/rejection by the authorized project owner for a specific decision item, with rationale/conditions/risks as applicable. | Does not by itself authorize implementation unless a separate explicit authorization record states so for a defined increment/scope. |
| **Implementation authorization** | A separate, explicit, narrowly scoped owner authorization record identifying exact increment(s), baseline, branch, allowed/prohibited changes, acceptance criteria, and date. | Does not authorize subsequent increments, does not resolve unrelated open decisions, and does not imply completion. |
| **Implementation completion** | Verified delivery of authorized scope meeting defined acceptance criteria with required evidence. | Not applicable here; no implementation is performed or authorized in Round 3.1. |

## 5. Non-negotiable constraints preserved

- PostgreSQL primary/system of record; modular monolith; core functional without MELIRA.
- MELIRA external SaaS only (explicit provider/model/region); no silent failover, no automatic transfer, no local inference, no local GPU.
- One unique monitored device = one licensed asset per tenant (multi-source same-device no duplicate licensing; equal device-type weight).
- Strict multi-tenancy: tenant authority only from trusted, verified, transaction-bound context; **never** client-supplied tenant IDs; **never** user-settable PostgreSQL GUC authorization; RLS defense-in-depth, not sufficient alone.
- Authoritative `core.asset_data_source` owning immutable `source_device_key_id`; aliases resolve to same binding (OD-002 Proposed). Identity/licensing idempotency ledger `(tenant_id, operation_type, idempotency_key)` distinct from `ingest.event_receipt` namespace dedup/provenance (OD-008/OD-013 Proposed). Typed lineage only. No exactly-once external delivery.
- OD-001–OD-013 and PD-001–PD-012 remain traceable and retain recorded statuses (no closure/approval invented). ADR 0006 remains **Proposed**. I-00–I-14 baseline classifications preserved.

## 6. Explicit statement — no implementation authorized

**No implementation is authorized by this document or by this Round 3.1 package.** Publication of these governance artifacts, planning readiness, technical feasibility discussion, or prior general project approval must not be interpreted as authorization for any implementation increment. Any future implementation requires a separate, explicit, owner-signed/recorded authorization for a narrowly defined increment and baseline, satisfying all stated prerequisites and exclusions.

## 7. Related Round 3.1 deliverables

- [POSTGRESQL_ROUND3_1_OWNER_DECISION_REGISTER.md](./POSTGRESQL_ROUND3_1_OWNER_DECISION_REGISTER.md)
- [POSTGRESQL_ROUND3_1_OWNER_DECISION_BRIEFS.md](./POSTGRESQL_ROUND3_1_OWNER_DECISION_BRIEFS.md)
- [POSTGRESQL_ROUND3_1_IMPLEMENTATION_AUTHORIZATION_MATRIX.md](./POSTGRESQL_ROUND3_1_IMPLEMENTATION_AUTHORIZATION_MATRIX.md)
- [POSTGRESQL_ROUND3_1_OWNER_DECISION_RECORD_TEMPLATE.md](./POSTGRESQL_ROUND3_1_OWNER_DECISION_RECORD_TEMPLATE.md)
- [POSTGRESQL_ROUND3_1_IMPLEMENTATION_AUTHORIZATION_TEMPLATE.md](./POSTGRESQL_ROUND3_1_IMPLEMENTATION_AUTHORIZATION_TEMPLATE.md)
- [POSTGRESQL_ROUND3_1_BLOCKER_AND_DEPENDENCY_MAP.md](./POSTGRESQL_ROUND3_1_BLOCKER_AND_DEPENDENCY_MAP.md)
- [POSTGRESQL_ROUND3_1_FINAL_REVIEW.md](./POSTGRESQL_ROUND3_1_FINAL_REVIEW.md)
