# CARES PostgreSQL Round 3 Migration and Deployment Strategy

**Status:** Proposed planning strategy only; **NOT IMPLEMENTED, NOT TESTED, NOT APPROVED FOR EXECUTION**. This document defines how future PostgreSQL schema implementation should be migrated and deployed if/when explicitly authorized. It does **not** provide DDL, migration files, executable scripts, or infrastructure changes.

**Related documents:** [POSTGRESQL_ROUND3_IMPLEMENTATION_PLAN.md](./POSTGRESQL_ROUND3_IMPLEMENTATION_PLAN.md), [POSTGRESQL_ROUND3_IMPLEMENTATION_WORK_BREAKDOWN.md](./POSTGRESQL_ROUND3_IMPLEMENTATION_WORK_BREAKDOWN.md), [POSTGRESQL_ROUND3_TEST_AND_ACCEPTANCE_PLAN.md](./POSTGRESQL_ROUND3_TEST_AND_ACCEPTANCE_PLAN.md), [POSTGRESQL_ROUND3_READINESS_AND_BLOCKER_MATRIX.md](./POSTGRESQL_ROUND3_READINESS_AND_BLOCKER_MATRIX.md), [POSTGRESQL_ROUND3_DEPENDENCY_MAP.md](./POSTGRESQL_ROUND3_DEPENDENCY_MAP.md), [POSTGRESQL_PHYSICAL_SCHEMA_DESIGN.md](./POSTGRESQL_PHYSICAL_SCHEMA_DESIGN.md), [POSTGRESQL_RLS_AND_TENANT_ISOLATION_DESIGN.md](./POSTGRESQL_RLS_AND_TENANT_ISOLATION_DESIGN.md), [POSTGRESQL_DATA_LIFECYCLE_AND_RETENTION.md](./POSTGRESQL_DATA_LIFECYCLE_AND_RETENTION.md).

## 1. Strategy objectives

- Deliver schema changes in **small, ordered, reversible-where-feasible increments** aligned with Round 2 dependencies and transaction boundaries.
- Preserve tenant isolation, identity/licensing correctness, audit/evidence integrity, and operational recoverability at every step.
- Ensure every migration unit is **idempotent at the migration-tooling level where possible**, traceable, reviewable, and accompanied by verification and rollback/recovery plans.
- Prevent runtime exposure of partially enforced tenant/security semantics.

## 2. Migration tooling and governance (proposed preconditions)

| Topic | Proposed requirement | Status/dependency |
|---|---|---|
| Migration framework | Select and standardize a versioned migration mechanism with checksum/history tracking, ordered execution, and environment promotion controls (tool choice not decided here) | Owner/engineering/DBA decision before I-01 execution |
| Version control and review | All future migration artifacts (when authorized) reviewed for correctness, security, tenant consistency, and rollback posture; no ad hoc production edits | Process prerequisite |
| Environment progression | Non-production/dev → integration/test → staging/pre-production (as available) → production, with gates per environment | Environment readiness evidence required |
| Change windows and approvals | Controlled windows for sensitive increments (RLS/privileges, contention-sensitive constraints/indexes, partitioning) | Ops/security approval |
| PostgreSQL baseline | Supported PostgreSQL version/features, extension availability, parameter baselines, and backup/PITR capability confirmed | DBA validation |

## 3. Migration sequencing strategy

### 3.1 Dependency-ordered domains

1. **Foundations:** schemas/namespaces, shared conventions/types (as approved), global/catalog tables (`core.tenant`, `core.external_identity_subject`, `core.role`, `core.role_permission`, `ingest.event_schema_reference`, `soc.threat_intelligence_reference`).
2. **Tenant access/config:** membership, role assignment, support access grant/approval, tenant configuration.
3. **Canonical identity and binding:** asset, data source, authoritative binding, optional dependent projection, aliases/claims; preserve OD-002 authority.
4. **Identity lifecycle and lineage:** resolution cases, lifecycle events, merge/split operations, typed lineage links, tombstones.
5. **Licensing/idempotency structures:** entitlement, usage state, license events/reservations, identity operation idempotency ledger (**structural planning only where semantics blocked; no final accounting enforcement without approvals**).
6. **Ingestion/events:** event receipt and security event with explicit namespace/dedup predicates bounded by OD-013.
7. **Processing/outbox:** outbox messages/attempts and optional work items, aligned with OD-009/PD-007 (no exactly-once claims).
8. **Audit/evidence and AI governance:** audit/evidence records, transitions/custody/versioning structures, AI config/consent/secret-reference/budget/audit tables (governance-gated).
9. **SOC operational:** alerts/cases/rules/versions/findings/observations.
10. **Hardening:** tenant-consistent composite FKs/uniques, CHECKs, partial/unique/expression indexes, contention-sensitive indexes (validated subset).
11. **Security enforcement rollout:** verified transaction-bound context mechanism (approved), least-privilege roles/grants, RLS policies/FORCE posture, pooling/session-safety controls — only after approval and validation.
12. **Deferred operations optimizations:** partitioning adoption, retention automation, maintenance tuning only with evidence and approvals.

### 3.2 Within-increment ordering rules
- Create referenced parent objects before child FKs; create base tables before dependent indexes/constraints that assume finalized structure where separable for safety (but do not expose unconstrained risky states to runtime traffic).
- Introduce uniqueness/idempotency/tenant-consistency constraints early enough to prevent invalid data during subsequent steps in the same controlled rollout.
- For high-risk or high-lock changes (large indexes, constraint validation, RLS enablement), use staged rollout patterns (e.g. create concurrently where supported/safe in future execution context, validate separately) only when explicitly planned and tested; never assume zero impact.
- Separate data-definition rollout from application behavior enablement; feature/runtime paths must remain disabled until verification gates pass.

## 4. Deployment and rollout strategy

| Stage | Purpose | Entry criteria | Exit/verification criteria |
|---|---|---|---|
| Design review gate | Confirm increment scope, dependencies, approvals, and rollback plan | Authorized increment, updated WBS/matrix | Signed review record, no unresolved mandatory blocker for scope |
| Non-production migration rehearsal | Execute and time migrations, capture locks/errors, validate scripts/process | Environment ready, backups/snapshots available | Successful apply/verify, documented timings/risks, rollback rehearsal evidence where feasible |
| Integration/functional validation | Verify schema objects, constraints, indexes, transaction/idempotency behavior in controlled tests | Rehearsal passed, test fixtures/procedures approved | Evidence per test/acceptance plan; no invariant violations |
| Security/isolation validation (required for tenant-affecting increments) | Negative cross-tenant tests, role/privilege checks, pooling/context reset, fail-closed behavior | Security mechanism approved/implemented for scope | All mandatory isolation tests pass; findings remediated or increment blocked |
| Staging/pre-production gate | Confirm operational readiness, monitoring, runbooks, and rollback posture | Prior gates passed | Owner/ops/security sign-off as required |
| Controlled production rollout (future, if authorized) | Apply approved increment with monitoring and rollback readiness | All required approvals and evidence | Post-deploy verification complete; no critical anomalies |

## 5. Rollback and recovery planning

- **Preferred approach:** forward-fix migrations for correctness issues when safe and auditable; maintain explicit down/rollback procedures only where technically feasible and non-destructive.
- **Irreversible considerations:** data-destructive changes, dropped constraints protecting invariants, purged history, or external side effects are unacceptable without exceptional authorization; evidence/audit/legal-hold data must not be rolled back in ways that violate retention/integrity requirements.
- **Backup/PITR:** take/confirm recoverable backups before risky increments; define recovery point objectives and restore validation steps per environment (targets open/assumption until approved).
- **Failure handling:** on migration failure, stop promotion, preserve logs/checksums/error evidence, assess partial state, and execute approved rollback/recovery/runbook; do not bypass failed verification gates.
- **Unknown/outbox reconciliation impacts:** deployment sequencing must not discard `timeout_unknown_commit`, `unknown` delivery, or unresolved reconciliation records.

## 6. Operational considerations

- **Lock/contention management:** schedule and monitor long-running DDL/index builds; avoid peak contention windows; assess impact on `tenant_license_usage_state`, ledger, receipt, and outbox hot paths.
- **Capacity/performance:** no claims made; collect baseline metrics and query plans during validation (OD-012).
- **RLS/pooling safety:** never deploy tenant-exposed runtime paths before verified context and RLS/privilege validation; ensure pool reset/transaction-local context behavior is tested.
- **Secrets and configuration:** secret references only (no plaintext), least-privilege credentials, controlled rotation/change management.
- **Auditability:** record who authorized/executed each increment, artifact hashes/versions, verification outcomes, and deviations.

## 7. Prohibited migration/deployment actions (this round)

- Creating/applying DDL, migration files, roles/policies, functions/triggers/procedures, or ORM/database implementation.
- Provisioning/modifying/executing against any database or environment.
- Using client-supplied tenant IDs or user-settable PostgreSQL GUCs for authorization/context.
- Force-pushing, history rewriting, or modifying Round 1.1/Round 2 publication branches.

## 8. Cross-references

See [POSTGRESQL_ROUND3_DEPENDENCY_MAP.md](./POSTGRESQL_ROUND3_DEPENDENCY_MAP.md) for sequencing/approval dependencies and [POSTGRESQL_ROUND3_FINAL_REVIEW.md](./POSTGRESQL_ROUND3_FINAL_REVIEW.md) for readiness classification and bounded first-increment assessment.
