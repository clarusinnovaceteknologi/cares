# CARES PostgreSQL Round 3.1 — Blocker and Dependency Map

**Status:** Proposed governance dependency analysis only; **NOT IMPLEMENTED, NOT TESTED, NOT AN APPROVAL**. Explains dependencies between unresolved decisions and implementation increments based on committed Round 3/Round 2 sources. No blocker is claimed resolved without source evidence; no implementation is authorized.

**Sources:** [POSTGRESQL_ROUND3_DEPENDENCY_MAP.md](./POSTGRESQL_ROUND3_DEPENDENCY_MAP.md), [POSTGRESQL_ROUND3_READINESS_AND_BLOCKER_MATRIX.md](./POSTGRESQL_ROUND3_READINESS_AND_BLOCKER_MATRIX.md), [POSTGRESQL_ROUND3_IMPLEMENTATION_PLAN.md](./POSTGRESQL_ROUND3_IMPLEMENTATION_PLAN.md), [POSTGRESQL_ROUND3_FINAL_REVIEW.md](./POSTGRESQL_ROUND3_FINAL_REVIEW.md), [POSTGRESQL_PHYSICAL_SCHEMA_OPEN_DECISIONS.md](./POSTGRESQL_PHYSICAL_SCHEMA_OPEN_DECISIONS.md).

## 1. Classification of blockers/prerequisites

| Type | Meaning in this map |
|---|---|
| **Hard blocker** | Prevents safe implementation/authorization for the affected increment(s) or runtime exposure until explicitly resolved/approved and validated as required. |
| **Conditional prerequisite** | Must be satisfied/validated before a specific bounded increment proceeds, but may not block unrelated planning artifacts; conditional readiness depends on it. |
| **Deferrable decision/validation** | Intentionally deferred pending evidence/governance; blocks affected automation/optimization/finalization but may not block all bounded preparatory planning where explicitly stated. |

## 2. Dependency map (by domain)

| Domain | Key unresolved items / dependencies | Affected increments | Classification | Rationale (source-backed) |
|---|---|---|---|---|
| Licensing, entitlement, quota accounting, reservations | OD-001, OD-003, OD-004, OD-008; ADR 0006 Proposed | I-06 (final semantics), I-13 (Ops 1/9 and ledger-coupled behavior) | **Hard blocker** for final semantics/runtime correctness | Accounting/enforcement, reservation/timeout/committed-reserved semantics, counter/reconciliation, and idempotency contract/coupling remain unapproved; ADR 0006 Proposed (readiness matrix/final review). |
| Identity, authoritative binding, lifecycle/lineage | OD-002, OD-005, OD-006, OD-007, OD-008 (ledger interactions), PD-004, PD-011 | I-04, I-05, downstream I-06/I-07/I-13 as applicable | **Conditional prerequisites / blockers by scope** | Authoritative binding/fingerprint/reinstall/merge-split/ledger semantics constrain structural and operational correctness; bounded preparation may be conditionally discussable only with stated approvals and without claiming final semantics. |
| Tenant isolation, verified context, RLS, privileges | PD-005, PD-006 (and OD-010 controlled-admin implications) | I-12, I-13 and any tenant-runtime exposure | **Hard blocker** | Verified transaction-bound context mechanism and RLS/ownership/role posture require security/DBA approval and negative isolation/pooling-reset evidence; no client-supplied tenant IDs or user-settable GUC authorization (readiness matrix/final review). |
| Idempotency and transactions/runtime operations | OD-008, OD-009, OD-001/003/004/005/010/011/013 as applicable; PD-007 | I-06, I-08, I-13 (Ops 1–13) | **Hard blocker** for runtime semantics/finalization | Operation coupling, outbox lease/fencing/unknown outcomes, and domain-specific unresolved semantics prevent authorized runtime implementation. |
| Ingestion/event dedup | OD-013, PD-008 | I-07 (Op 10), downstream processing | **Conditional prerequisite / partial hard blocker** for finalized per-connector dedup | Connector namespace/fallback predicates remain open/partial; dedup must remain distinct from identity/licensing ledger. |
| Outbox processing and delivery behavior | OD-009, PD-007 | I-08, I-13 (Ops 11/12) | **Conditional prerequisite / hard blocker for runtime** | Lease/fencing/retry/unknown-delivery semantics and claim mechanism require approval/validation; no exactly-once external delivery. |
| Audit, evidence, AI governance, retention/legal hold | OD-010, OD-011, PD-011 | I-09, I-14, evidence lifecycle/controlled transitions | **Deferrable governance prerequisites / hard for automation-finalization** | Legal/privacy/security/compliance approvals and retention classes required before automation/final enforcement specifics; release-sensitive integrity/legal-hold constraints apply. |
| SOC scope, indexing, performance, partitioning | OD-012, PD-009, PD-010, PD-012, PD-001/003/008 as applicable | I-10, I-11, I-14 | **Conditional prerequisites and deferrable validations** | Workload/index/partition thresholds and scope/access modeling require evidence/governance; no premature optimization claims. |
| Physical conventions/cross-cutting | PD-001, PD-002, PD-003, PD-004, PD-011, PD-012 | I-01–I-11 (as applicable) | **Conditional prerequisites** | Convention/mechanism decisions affect correctness, isolation clarity, and maintainability; must be approved/validated before dependent implementation. |

## 3. Increment dependency chain (preserved baseline)

| Increment | Baseline classification | Direct prerequisites | Notable blocking dependencies | Notes |
|---|---|---|---|---|
| I-00 | Conditionally ready | Round 2 baseline, owner intent | None formal (preconditions unresolved) | No implementation authorized; see authorization matrix. |
| I-01 | Conditionally ready | I-00; Physical schema §3 | PD-001, PD-002, PD-004 | No implementation authorized; see authorization matrix. |
| I-02 | Conditionally ready | I-01 | PD-012 (scope-sensitive elements) | No implementation authorized; see authorization matrix. |
| I-03 | Conditionally ready | I-02; PD-003 | PD-003 | No implementation authorized; see authorization matrix. |
| I-04 | Conditionally ready | I-03 | OD-002, OD-006, OD-007, PD-004, PD-011 | No implementation authorized; see authorization matrix. |
| I-05 | Conditionally ready | I-04 | OD-005, OD-007 | No implementation authorized; see authorization matrix. |
| I-06 | Blocked (final semantics) / conditionally ready for bounded structural planning only | I-04, I-05 | OD-001, OD-003, OD-004, OD-008, PD-001/002/003; ADR 0006 Proposed | No implementation authorized; see authorization matrix. |
| I-07 | Conditionally ready | I-02, I-04 | OD-013, PD-008 | No implementation authorized; see authorization matrix. |
| I-08 | Conditionally ready | I-07 | OD-009, PD-007 | No implementation authorized; see authorization matrix. |
| I-09 | Conditionally ready | I-03, I-04, I-08 | OD-010, OD-011, PD-011 | No implementation authorized; see authorization matrix. |
| I-10 | Conditionally ready | I-02, I-04, I-07 | OD-010, OD-012, PD-009, PD-012 | No implementation authorized; see authorization matrix. |
| I-11 | Conditionally ready | I-02–I-10 | PD-003, PD-008, PD-009, OD-012 | No implementation authorized; see authorization matrix. |
| I-12 | Blocked | I-11 | PD-005, PD-006, OD-010 (controlled admin implications) | No implementation authorized; see authorization matrix. |
| I-13 | Blocked / out of Round 3 scope | I-12 and domain increments | OD-001,003,004,005,008,009,010,011,013 and relevant PDs | No implementation authorized; see authorization matrix. |
| I-14 | Deferred / Blocked by evidence & governance | I-11, operational evidence | OD-010, OD-012, PD-010 | No implementation authorized; see authorization matrix. |

## 4. Hard blockers preventing tenant-runtime authorization/readiness (current state)

- **PD-005/PD-006:** verified tenant-context DB mechanism, RLS/ownership/role hardening, and required negative isolation/pooling-reset evidence not approved/validated (blocks I-12 and tenant-runtime exposure).
- **OD-001/003/004/008 (and ADR 0006 Proposed):** licensing/idempotency accounting/contract semantics not finalized/approved (blocks I-06 final semantics and correctness-critical runtime behavior).
- **OD-009 and related runtime semantics:** outbox/runtime operation prerequisites unresolved for I-13 (blocked/out of scope).
- **Owner authorization:** no explicit implementation authorization record exists for any increment (all I-00–I-14 unauthorized).

## 5. Non-resolution statement

No blocker, OD, PD, or ADR item is resolved, approved, deferred-by-owner, or closed by this map. Contradictions or missing committed source details (e.g. committed logical open-decision register/ADR 0006 markdown source not present at baseline) must be reviewed and resolved through explicit owner/governance actions recorded in the repository.
