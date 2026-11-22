# CARES PostgreSQL Round 3 Dependency Map

**Status:** Proposed planning artifact only; **NOT IMPLEMENTED, NOT TESTED, NOT APPROVED FOR EXECUTION**. This map visualizes implementation sequencing, component dependencies, and approval/validation gates derived from Round 2 baselines and recorded open decisions. It does not change OD/PD/ADR statuses or authorize execution.

**Related documents:** [POSTGRESQL_ROUND3_IMPLEMENTATION_PLAN.md](./POSTGRESQL_ROUND3_IMPLEMENTATION_PLAN.md), [POSTGRESQL_ROUND3_IMPLEMENTATION_WORK_BREAKDOWN.md](./POSTGRESQL_ROUND3_IMPLEMENTATION_WORK_BREAKDOWN.md), [POSTGRESQL_ROUND3_MIGRATION_AND_DEPLOYMENT_STRATEGY.md](./POSTGRESQL_ROUND3_MIGRATION_AND_DEPLOYMENT_STRATEGY.md), [POSTGRESQL_ROUND3_TEST_AND_ACCEPTANCE_PLAN.md](./POSTGRESQL_ROUND3_TEST_AND_ACCEPTANCE_PLAN.md), [POSTGRESQL_ROUND3_READINESS_AND_BLOCKER_MATRIX.md](./POSTGRESQL_ROUND3_READINESS_AND_BLOCKER_MATRIX.md), [POSTGRESQL_ROUND3_CHANGELOG.md](./POSTGRESQL_ROUND3_CHANGELOG.md), [POSTGRESQL_ROUND3_FINAL_REVIEW.md](./POSTGRESQL_ROUND3_FINAL_REVIEW.md).

## 1. Phase and increment dependency flow

```mermaid
flowchart TD
  A[I-00 Authorization & environment readiness<br/>Conditionally ready] --> B[I-01 Schemas & conventions<br/>PD-001/002/004]
  B --> C[I-02 Global/catalog foundations]
  C --> D[I-03 Tenant access & configuration<br/>PD-003]
  D --> E[I-04 Canonical asset & authoritative binding<br/>OD-002/006/007, PD-004/011]
  E --> F[I-05 Identity lifecycle, typed lineage, tombstones<br/>OD-005/007]
  E --> G[I-06 Licensing, usage, ledger, reservation<br/>BLOCKED final semantics: OD-001/003/004/008]
  F --> G
  E --> H[I-07 Ingestion & events<br/>OD-013, PD-008]
  H --> I[I-08 Outbox & processing<br/>OD-009, PD-007]
  D --> J[I-09 Audit/evidence & AI governance<br/>OD-010/011]
  E --> J
  I --> J
  C --> K[I-10 SOC operational structures<br/>OD-010/012, PD-012]
  E --> K
  H --> K
  F --> L[I-11 Integrity & index hardening<br/>PD-003/008/009, OD-012]
  G --> L
  J --> L
  K --> L
  L --> M[I-12 Verified context, roles/privileges, RLS<br/>BLOCKED: PD-005/006]
  M --> N[I-13 Transactional/runtime semantics<br/>BLOCKED / out of scope]
  L --> O[I-14 Partitioning, retention automation, tuning<br/>DEFERRED: OD-010/012, PD-010]

  classDef blocked fill:#fff3cd,stroke:#b58900,color:#333;
  classDef deferred fill:#eef,stroke:#667,color:#333;
  class G,M,N blocked;
  class O deferred;
```

## 2. Decision and approval gate map

```mermaid
flowchart LR
  subgraph Identity_Licensing[Identity & licensing semantics]
    OD002[OD-002 Binding authority<br/>Proposed]
    OD001[OD-001 ADR 0006 acceptance<br/>Proposed]
    OD003[OD-003 Reservation semantics<br/>Proposed]
    OD004[OD-004 Counter semantics<br/>Proposed]
    OD005[OD-005 Merge/split authority<br/>Proposed]
    OD006[OD-006 Fingerprint protection/rotation<br/>Proposed]
    OD007[OD-007 Reinstall/re-enrollment<br/>Proposed]
    OD008[OD-008 Idempotency contract<br/>Proposed]
  end

  subgraph Ingest_Outbox[Ingestion & async delivery]
    OD013[OD-013 Event namespace/fallback<br/>Proposed/open]
    OD009[OD-009 Outbox lease/fencing/unknown<br/>Proposed]
  end

  subgraph Governance_Ops[Governance & operations]
    OD010[OD-010 Retention/legal hold/deletion<br/>Deferred]
    OD011[OD-011 AI consent/classification/budget<br/>Deferred]
    OD012[OD-012 Workload/index/partition validation<br/>Deferred]
  end

  subgraph Physical_Security[Physical/security mechanisms]
    PD005[PD-005 Verified tenant context mechanism<br/>Proposed]
    PD006[PD-006 RLS/FORCE hardening details<br/>Deferred]
    PD010[PD-010 Partitioning adoption<br/>Deferred]
  end

  OD002 --> I4[I-04/I-05 Binding & lineage]
  OD006 --> I4
  OD007 --> I4
  OD005 --> I5[I-05/I-06 Merge/split/licensing effects]
  OD001 --> I6[I-06 Licensing final semantics]
  OD003 --> I6
  OD004 --> I6
  OD008 --> I6
  OD013 --> I7[I-07 Event receipt dedup]
  OD009 --> I8[I-08 Outbox behavior]
  OD010 --> I9[I-09/I-14 Evidence/retention]
  OD011 --> I9
  OD012 --> I11[I-11/I-14 Index/partition validation]
  PD005 --> I12[I-12 RLS/runtime isolation]
  PD006 --> I12
  PD010 --> I14[I-14 Partitioning adoption]
```

## 3. Domain-to-operation dependency view

| Round 2 operation | Primary tables/domains (planned dependency groups) | Key prerequisites / gates |
|---|---|---|
| Op 1 New canonical asset registration | ledger, asset, asset_data_source, optional source_device_key, alias/claim/lifecycle, usage/entitlement/license/reservation, audit | I-04–I-06, I-09; OD-001/002/003/004/008; verified context/RLS for runtime |
| Op 2 Existing asset attachment | ledger, asset, asset_data_source, alias/claim/lifecycle, audit | I-04–I-06; OD-002/008; no duplicate licensed usage invariant |
| Op 3 Fingerprint alias creation | alias, authoritative binding, claim/lifecycle, audit | I-04; OD-006; PD-011 representation decisions |
| Op 4 Fingerprint rotation | alias, binding, lifecycle, audit | I-04; OD-006/007; immutable `source_device_key_id` |
| Op 5 Identity conflict/pending resolution | resolution case, claim, asset/binding reads, lifecycle, audit | I-04/I-05; OD-007; no auto-billing/incorrect binding |
| Op 6 Asset merge | merge op, assets, typed lineage, tombstone, binding/alias/claim reassignment, usage/license events, ledger, audit | I-04–I-06, I-09; OD-005/003/004/008; typed lineage integrity |
| Op 7 Asset split | split op, assets, typed lineage, tombstone as applicable, reassignment, usage/license events, ledger, audit | I-04–I-06, I-09; OD-005/003/004/008; capacity/evidence rules |
| Op 8 Deactivation/reactivation/removal | asset, lifecycle/license events, usage state, tombstone, binding status, ledger, audit | I-04–I-06; OD-003/004/008 |
| Op 9 Quota allocation/reservation/release | usage state, entitlement, reservation, license event, ledger, audit | I-06; OD-001/003/004/008; contention-safe locking design |
| Op 10 Event ingestion acceptance | event_receipt, security_event, schema refs, data source/binding/asset attribution, optional outbox/work item, audit | I-04, I-07, I-08; OD-013/PD-008; namespace-scoped dedup |
| Op 11 Outbox claim and processing | outbox_message, outbox_attempt, optional work item, audit | I-08; OD-009/PD-007; claim/lease validation |
| Op 12 Outbox external delivery unknown outcome | outbox_attempt, outbox_message, audit | I-08; OD-009; unknown != success, no exactly-once |
| Op 13 Forensic evidence creation/transition | forensic evidence record/version/custody/authorization, audit | I-09; OD-010; controlled transitions and legal-hold constraints |

## 4. Traceability matrix (planning level)

| Traceability dimension | Source baseline | Round 3 planning artifact(s) |
|---|---|---|
| Logical entities and Round 1.1 corrections | Logical model, ERD, transaction boundaries, OD register, Round 1.1 audit | All Round 3 docs; especially plan/WBS/matrix |
| Physical tables (50), schemas, constraints, indexes | Physical schema design, ERD, index strategy | Plan, WBS, migration strategy, test plan, dependency map |
| Transaction boundaries (Ops 1–13) | Physical transaction design | Plan, WBS, migration strategy, test plan, dependency map, final review |
| Tenant isolation and RLS posture | RLS/tenant isolation design, security architecture, threat model | Plan, WBS, migration strategy, test plan, readiness matrix, final review |
| Lifecycle/retention/maintenance | Data lifecycle and retention design | Plan, migration strategy, test plan, readiness matrix, dependency map |
| Open decisions and physical decisions | OD register, physical open decisions, Round 2 final review | Readiness matrix, dependency map, changelog, final review |
| ADR/roadmap/project constraints | ADR 0001–0006, roadmap, project status, requirements traceability | Plan, changelog, final review (no status changes) |
