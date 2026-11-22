
> **Round 3.2.1 fidelity-correction note (2026-11-22, documentation-only):** This document remains the **Round 3.1 historical owner-decision brief set** (proposed governance briefs only; not owner decisions, not approvals, not implementation authorization). It must not be read as contradicting or superseding the **authoritative, fidelity-corrected owner-approved principles and bounded conditions for OD-001–OD-013** recorded in [POSTGRESQL_ROUND3_2_OWNER_DECISION_REGISTER.md](./POSTGRESQL_ROUND3_2_OWNER_DECISION_REGISTER.md) and reconciled in [POSTGRESQL_ROUND3_2_IMPLEMENTATION_AUTHORIZATION_MATRIX.md](./POSTGRESQL_ROUND3_2_IMPLEMENTATION_AUTHORIZATION_MATRIX.md), [POSTGRESQL_ROUND3_2_DEPENDENCY_AND_BLOCKER_MAP.md](./POSTGRESQL_ROUND3_2_DEPENDENCY_AND_BLOCKER_MAP.md), [POSTGRESQL_ROUND3_2_FINAL_REVIEW.md](./POSTGRESQL_ROUND3_2_FINAL_REVIEW.md), and [adr/0006-atomic-per-tenant-asset-licensing.md](./adr/0006-atomic-per-tenant-asset-licensing.md). Where this historical brief contains preliminary framing that differs from those authoritative Round 3.2.1 records, the Round 3.2.1 records govern. PD-001–PD-012 remain unresolved/deferred where applicable; ADR 0006 formal status remains **Proposed**; **no implementation increment is authorized**.

# CARES PostgreSQL Round 3.1 — Owner Decision Briefs

**Status:** Proposed governance briefs only; **NOT IMPLEMENTED, NOT TESTED, NOT APPROVED FOR EXECUTION, NOT OWNER DECISIONS**. Prepared to support owner review of unresolved items. Source-backed alternatives are cited from committed repository documents; Copilot analysis is explicitly labeled advisory and non-authoritative. No new alternative is presented as approved.

**Traceability:** OD-001–OD-013 and PD-001–PD-012 preserved with recorded statuses from committed sources. **Source gaps noted:** committed `docs/POSTGRESQL_SCHEMA_OPEN_DECISIONS.md` and committed ADR 0006 markdown source are not present at baseline `ee6e005`; briefs rely on committed carry-forward/review/planning sources and identify where information is insufficient.

## 1. Logical/open decision briefs (OD-001–OD-013)

### OD-001 — ADR 0006 acceptance and unresolved concurrency/quota/timeout ambiguity
- **Recorded status (preserved):** Proposed / pending ADR acceptance (ADR 0006 remains Proposed)
- **Primary sources (committed):** docs/POSTGRESQL_PHYSICAL_SCHEMA_OPEN_DECISIONS.md; docs/POSTGRESQL_ROUND3_READINESS_AND_BLOCKER_MATRIX.md; docs/POSTGRESQL_ROUND3_FINAL_REVIEW.md; docs/POSTGRESQL_PHYSICAL_SCHEMA_ROUND2_FINAL_REVIEW.md
- **Problem / unresolved question:** Licensing accounting/enforcement semantics and schema-level interpretations (including concurrency/quota/timeout ambiguity) remain unaccepted/unfinalized in the context of ADR 0006.
- **Why a decision is needed:** Licensing counters, reservation/timeout behavior, reconciliation semantics, and correctness-critical transaction behavior depend on accepted semantics; I-06 final semantics and I-13 are constrained.
- **Viable alternatives/options supported by source documents:** Sources record the open/proposed decision and dependency but do not provide a committed, fully enumerated approved option set in available files at this baseline.
- **Copilot analysis (not a source-backed decision or approval):** Copilot analysis (advisory, not approved): owner review should compare (a) accepting ADR 0006 with explicitly bounded schema/runtime interpretations, (b) revising ADR 0006 before acceptance, or (c) formally deferring with explicit non-implementation constraints; each must preserve one-device-one-licensed-asset and no-finalized-accounting-without-approval invariants.
- **Consequences / implications:** Affects licensing/entitlement/ledger/reservation design finalization, operational reconciliation, and safe authorization of runtime licensing behavior.
- **Dependencies and affected increments:** Depends on/interacts with OD-003, OD-004, OD-008, ADR 0006 (Proposed). Affects I-06, I-13.
- **Risks if unresolved or incorrectly assumed:** Risk of incorrect licensing accounting/enforcement, tenant-commercial disputes, and invariant violations if assumed final.
- **Information gaps / owner clarification needed:** Committed logical open-decision register and ADR 0006 markdown source not present at baseline; authoritative option details/rationale text may be incomplete. **Requires owner clarification and formal governance review.**
- **Blocking characterization:** **Hard blocker** for I-06 final semantics and licensing/runtime correctness (I-13).

### OD-002 — Authoritative stable binding ownership and optional dependent `source_device_key` projection
- **Recorded status (preserved):** Proposed (open approval)
- **Primary sources (committed):** docs/POSTGRESQL_PHYSICAL_SCHEMA_OPEN_DECISIONS.md; docs/POSTGRESQL_ROUND3_READINESS_AND_BLOCKER_MATRIX.md; docs/POSTGRESQL_ROUND3_IMPLEMENTATION_PLAN.md
- **Problem / unresolved question:** Final approval of `core.asset_data_source` as authoritative stable binding owning immutable `source_device_key_id`, and posture for optional dependent `core.source_device_key`, remains open.
- **Why a decision is needed:** Binding authority/uniqueness underpins identity resolution, licensing association, and prevention of competing/mutable identity sources.
- **Viable alternatives/options supported by source documents:** Source-backed direction: authoritative binding owned by `core.asset_data_source` with immutable `source_device_key_id`; optional dependent `source_device_key` projection may be materialized as strict 1:1 non-authoritative or omitted (PD-004 proposed).
- **Copilot analysis (not a source-backed decision or approval):** Copilot analysis (advisory): prefer the source-recommended authoritative model and avoid separate mutable authority; if projection is materialized, enforce strict parity/immutability constraints and review divergence risks.
- **Consequences / implications:** Impacts schema constraints, transaction checks, alias/claim workflows, and downstream licensing/lineage integrity.
- **Dependencies and affected increments:** Dependencies/interactions: OD-006, OD-007, PD-004. Affects I-04 and downstream increments.
- **Risks if unresolved or incorrectly assumed:** Competing identity authority or mutable stable keys could break dedup/licensing/lineage correctness and tenant trust.
- **Information gaps / owner clarification needed:** Original logical register details unavailable in committed baseline; final sign-off criteria require owner/architecture/security confirmation.
- **Blocking characterization:** **Conditional prerequisite / blocker for final sign-off** of identity-binding structures and operations (I-04+).

### OD-003 — Pending reservation behavior, timeout/release, and committed/reserved counter semantics
- **Recorded status (preserved):** Proposed (open approval)
- **Primary sources (committed):** docs/POSTGRESQL_PHYSICAL_SCHEMA_OPEN_DECISIONS.md; docs/POSTGRESQL_ROUND3_READINESS_AND_BLOCKER_MATRIX.md
- **Problem / unresolved question:** Reservation lifecycle (pending/timeout/release) and committed vs reserved counter semantics are not finalized.
- **Why a decision is needed:** Correct quota allocation, release on failure/timeout, reconciliation, and user-visible licensing behavior depend on these semantics.
- **Viable alternatives/options supported by source documents:** Sources identify the unresolved areas and affected structures (`asset_license_reservation`, `tenant_license_usage_state`, Ops 1/9) but do not document a committed approved option set at baseline.
- **Copilot analysis (not a source-backed decision or approval):** Copilot analysis (advisory): evaluate bounded timeout/expiry with deterministic reconciliation and auditable state transitions; avoid implicit finalization; align with OD-001/004/008 and concurrency/idempotency requirements.
- **Consequences / implications:** Impacts I-06 structures/semantics and future transaction behavior (I-13).
- **Dependencies and affected increments:** OD-001, OD-004, OD-008. Affects I-06, Ops 1/9.
- **Risks if unresolved or incorrectly assumed:** Risk of leaked reservations, double counting, denial of service, or incorrect entitlement enforcement.
- **Information gaps / owner clarification needed:** Detailed alternatives/thresholds require owner/commercial/ops input; **information gap** at committed baseline.
- **Blocking characterization:** **Hard blocker** for final licensing accounting/enforcement semantics in affected scope.

### OD-004 — Tenant-level authoritative counter scope and recomputation/reconciliation semantics
- **Recorded status (preserved):** Proposed (open approval)
- **Primary sources (committed):** docs/POSTGRESQL_PHYSICAL_SCHEMA_OPEN_DECISIONS.md; docs/POSTGRESQL_ROUND3_READINESS_AND_BLOCKER_MATRIX.md
- **Problem / unresolved question:** Authoritative tenant-level counter scope and recomputation/reconciliation formulas/semantics are unresolved.
- **Why a decision is needed:** Consistent, auditable license usage accounting and recovery from partial/failed operations require defined counter authority and reconciliation rules.
- **Viable alternatives/options supported by source documents:** Sources identify affected usage-state/reconciliation structures and planning impact; no committed approved formula set recorded at baseline.
- **Copilot analysis (not a source-backed decision or approval):** Copilot analysis (advisory): define a single authoritative accounting source per tenant/scope with deterministic recomputation from immutable/auditable events where feasible, reconciled against ledger outcomes under approved OD-008 semantics.
- **Consequences / implications:** Impacts I-06, reconciliation operations, reporting correctness, and commercial trust.
- **Dependencies and affected increments:** OD-001, OD-003, OD-008. Affects I-06 and related operations.
- **Risks if unresolved or incorrectly assumed:** Inconsistent counters can cause over/under-licensing and audit/compliance issues.
- **Information gaps / owner clarification needed:** Requires commercial/product/finance/governance input and explicit formulas; **information gap**.
- **Blocking characterization:** **Hard blocker** for final counter formulas and reconciliation implementation rules.

### OD-005 — Merge/split authorization, evidence, and licensing effects
- **Recorded status (preserved):** Proposed (open approval)
- **Primary sources (committed):** docs/POSTGRESQL_PHYSICAL_SCHEMA_OPEN_DECISIONS.md; docs/POSTGRESQL_ROUND3_READINESS_AND_BLOCKER_MATRIX.md
- **Problem / unresolved question:** Authorization, evidentiary requirements, and licensing effects for merge/split operations remain unapproved.
- **Why a decision is needed:** Merge/split changes canonical identity relationships and can affect licensing counts, lineage, and auditability.
- **Viable alternatives/options supported by source documents:** Source-backed invariants: typed lineage only, tombstones/lifecycle operations modeled, no canonical ID reuse; operational policy/effects pending.
- **Copilot analysis (not a source-backed decision or approval):** Copilot analysis (advisory): require explicit authorized actor/evidence, atomic transactional coupling with ledger/licensing effects per approved OD-001/003/004/008, and irreversible/auditable lineage records; reject implicit merges.
- **Consequences / implications:** Impacts I-05, I-06, Ops 6/7, lineage/tombstone correctness.
- **Dependencies and affected increments:** OD-007, OD-008 and licensing dependencies as applicable. Affects I-05 and licensing semantics.
- **Risks if unresolved or incorrectly assumed:** Unauthorized or incorrect merges/splits can corrupt identity history and licensing state.
- **Information gaps / owner clarification needed:** Policy/evidence/licensing-effect specifics not fully documented in committed baseline; **owner clarification required**.
- **Blocking characterization:** **Conditional prerequisite/blocker** for final operational merge/split policy and edge-case enforcement.

### OD-006 — Fingerprint hashing/protection, key custody, rotation overlap, and reassignment safeguards
- **Recorded status (preserved):** Proposed (open approval)
- **Primary sources (committed):** docs/POSTGRESQL_PHYSICAL_SCHEMA_OPEN_DECISIONS.md; docs/POSTGRESQL_ROUND3_READINESS_AND_BLOCKER_MATRIX.md
- **Problem / unresolved question:** Approved fingerprint protection representation, custody, rotation overlap, and reassignment safeguards are unresolved.
- **Why a decision is needed:** Fingerprints/aliases are security-sensitive identity inputs; weak protection or unsafe rotation can enable reassignment/collision or leakage.
- **Viable alternatives/options supported by source documents:** Source-backed elements: fingerprint/alias uniqueness and rotation procedures are impacted; PD-011 proposes algorithm metadata plus consistent representation pending review.
- **Copilot analysis (not a source-backed decision or approval):** Copilot analysis (advisory): use approved cryptographic protections and custody boundaries, define overlap windows and revocation/reassignment controls, and validate uniqueness predicates under rotation scenarios.
- **Consequences / implications:** Impacts I-04, Ops 3/4, storage/representation choices (PD-011), and security posture.
- **Dependencies and affected increments:** OD-002, OD-007, PD-011.
- **Risks if unresolved or incorrectly assumed:** Risk of identity spoofing/reassignment, privacy exposure, or operational lockout during rotation.
- **Information gaps / owner clarification needed:** Cryptographic/custody specifics and overlap policy require security/ops approval; **information gap**.
- **Blocking characterization:** **Conditional prerequisite** for secure identity-binding/fingerprint handling.

### OD-007 — Reinstall/re-enrollment and controlled identity-reset handling
- **Recorded status (preserved):** Proposed (open approval)
- **Primary sources (committed):** docs/POSTGRESQL_PHYSICAL_SCHEMA_OPEN_DECISIONS.md; docs/POSTGRESQL_ROUND3_READINESS_AND_BLOCKER_MATRIX.md
- **Problem / unresolved question:** Lifecycle rules for reinstall/re-enrollment and controlled identity reset/rebinding are unresolved.
- **Why a decision is needed:** These events are common operational cases and can affect whether activity maps to the same licensed asset or requires governed resolution.
- **Viable alternatives/options supported by source documents:** Sources identify impact on resolution/claim/binding workflows and alias rotation/rebinding rules (I-04/I-05).
- **Copilot analysis (not a source-backed decision or approval):** Copilot analysis (advisory): preserve one-device-one-licensed-asset-per-tenant semantics, require auditable controlled reset paths, and prevent silent creation of duplicate licensed assets for the same monitored device.
- **Consequences / implications:** Impacts I-04/I-05 workflows, lifecycle/tombstone handling, and support operations.
- **Dependencies and affected increments:** OD-002, OD-005, OD-006.
- **Risks if unresolved or incorrectly assumed:** Incorrect handling may duplicate licensing, lose continuity, or enable abuse.
- **Information gaps / owner clarification needed:** Detailed workflow states/criteria require architecture/product/operations decisions; **information gap**.
- **Blocking characterization:** **Conditional prerequisite** for lifecycle workflow finalization.

### OD-008 — Formal idempotency contract and coupling mode
- **Recorded status (preserved):** Proposed (open approval)
- **Primary sources (committed):** docs/POSTGRESQL_PHYSICAL_SCHEMA_OPEN_DECISIONS.md; docs/POSTGRESQL_ROUND3_READINESS_AND_BLOCKER_MATRIX.md; docs/POSTGRESQL_ROUND3_FINAL_REVIEW.md
- **Problem / unresolved question:** Formal contract for identity/licensing idempotency (scope, canonical hash, states, replay/conflict, timeout/unknown-commit, retention) and coupling mode remains unapproved.
- **Why a decision is needed:** Ledger-backed operations (Ops 1–9) require deterministic, auditable behavior under retries/concurrency and must remain distinct from event receipt dedup.
- **Viable alternatives/options supported by source documents:** Source-backed baseline: ledger scope `(tenant_id, operation_type, idempotency_key)`, documented proposed state/coupling shape in physical design; must remain distinct from `ingest.event_receipt` namespace dedup/provenance.
- **Copilot analysis (not a source-backed decision or approval):** Copilot analysis (advisory): formalize deterministic canonicalization/hash inputs, explicit state transitions for in-progress/committed/failed-terminal/timeout-unknown-commit, replay/conflict responses, retention/reconciliation hooks, and atomic coupling boundaries as approved.
- **Consequences / implications:** Impacts I-06 and all ledger-coupled runtime operations (I-13), correctness under retries/failures.
- **Dependencies and affected increments:** OD-001/003/004/005/009 interactions as applicable. Affects I-06, Ops 1–9.
- **Risks if unresolved or incorrectly assumed:** Ambiguous idempotency can cause duplicate effects, lost effects, or irreconcilable unknown outcomes.
- **Information gaps / owner clarification needed:** Formal approval text/complete contract details require owner/architecture sign-off; **information gap** relative to committed logical register.
- **Blocking characterization:** **Hard blocker** for finalized ledger semantics and runtime correctness in coupled operations.

### OD-009 — Outbox leasing/fencing, dispatch ownership, retry/claim semantics, and unknown-delivery handling
- **Recorded status (preserved):** Proposed (open approval)
- **Primary sources (committed):** docs/POSTGRESQL_PHYSICAL_SCHEMA_OPEN_DECISIONS.md; docs/POSTGRESQL_ROUND3_READINESS_AND_BLOCKER_MATRIX.md
- **Problem / unresolved question:** Approved outbox claim/lease/fencing/retry and unknown-delivery handling semantics remain unresolved.
- **Why a decision is needed:** Reliable at-least-once processing with idempotent consumers requires explicit claim ownership, fencing, retries, and visibility of unknown outcomes.
- **Viable alternatives/options supported by source documents:** Source-backed constraints: no exactly-once external delivery; `processing.outbox_message`/`outbox_attempt` and claim/index patterns proposed; PD-007 proposes mechanism options pending validation.
- **Copilot analysis (not a source-backed decision or approval):** Copilot analysis (advisory): combine lease tokens/expiry with atomic state transitions and fencing to prevent concurrent double-processing claims; define bounded retry/backoff and explicit unknown-delivery reconciliation states.
- **Consequences / implications:** Impacts I-08 and outbox runtime behavior (Ops 11/12, I-13).
- **Dependencies and affected increments:** OD-008, PD-007, OD-012 for validation.
- **Risks if unresolved or incorrectly assumed:** Risk of duplicate side effects, stuck messages, or lost visibility of delivery uncertainty.
- **Information gaps / owner clarification needed:** Operational SLO targets and final mechanics require engineering/reliability approval and validation; **information gap**.
- **Blocking characterization:** **Conditional prerequisite / hard blocker for runtime** outbox processing semantics.

### OD-010 — Retention/legal-hold/deletion classes for audit, evidence, events, and telemetry
- **Recorded status (preserved):** Deferred / pending governance approval
- **Primary sources (committed):** docs/POSTGRESQL_PHYSICAL_SCHEMA_OPEN_DECISIONS.md; docs/POSTGRESQL_ROUND3_READINESS_AND_BLOCKER_MATRIX.md
- **Problem / unresolved question:** Approved retention classes, legal-hold handling, deletion/archive rules, and automation eligibility are not finalized.
- **Why a decision is needed:** Compliance, privacy, evidentiary integrity, storage cost, and partition/drop eligibility depend on governed lifecycle rules.
- **Viable alternatives/options supported by source documents:** Sources mark deferred/pending governance approval and identify impacts on retention matrix, lifecycle automation, evidence handling (I-09/I-14).
- **Copilot analysis (not a source-backed decision or approval):** Copilot analysis (advisory): classify data by purpose/sensitivity/legal basis, define hold precedence over deletion, and gate automation behind approved policies and tested runbooks; do not infer durations.
- **Consequences / implications:** Impacts I-09, I-14, operational/compliance posture.
- **Dependencies and affected increments:** OD-011, OD-012, PD-010.
- **Risks if unresolved or incorrectly assumed:** Premature deletion/retention can violate legal/compliance obligations or destroy evidence; indefinite retention increases risk/cost.
- **Information gaps / owner clarification needed:** Specific classes/durations/hold procedures require legal/compliance/privacy/security decisions; **information gap**.
- **Blocking characterization:** **Deferrable governance prerequisite** (hard for automation/final lifecycle enforcement).

### OD-011 — AI consent, data-classification/redaction, budget/quota, and provider-policy persistence details
- **Recorded status (preserved):** Deferred / pending policy and privacy approval
- **Primary sources (committed):** docs/POSTGRESQL_PHYSICAL_SCHEMA_OPEN_DECISIONS.md; docs/POSTGRESQL_ROUND3_READINESS_AND_BLOCKER_MATRIX.md
- **Problem / unresolved question:** Approved consent, classification/redaction, budget/quota, and provider-policy persistence/enforcement details for AI governance remain unresolved.
- **Why a decision is needed:** AI interactions must satisfy privacy/policy controls and MELIRA external SaaS constraints; persistence must support governance and auditability.
- **Viable alternatives/options supported by source documents:** Source-backed constraints: MELIRA external SaaS only (explicit provider/model/region), no silent failover/automatic transfer/local inference/local GPU; governance structures impacted in I-09.
- **Copilot analysis (not a source-backed decision or approval):** Copilot analysis (advisory): define data-classification and redaction/consent gates before transmission, persist auditable policy/budget decisions and provider/model/region selections, and prohibit implicit provider changes.
- **Consequences / implications:** Impacts I-09 and future AI-governed behaviors.
- **Dependencies and affected increments:** OD-010; product/privacy/legal/security/commercial governance.
- **Risks if unresolved or incorrectly assumed:** Risk of unauthorized data transfer, policy violations, or uncontrolled cost/usage.
- **Information gaps / owner clarification needed:** Policy specifics and enforcement rules require owner/privacy/legal approval; **information gap**.
- **Blocking characterization:** **Deferrable governance prerequisite** (blocks final enforcement specifics).

### OD-012 — Retention, partitioning, and workload/index validation
- **Recorded status (preserved):** Deferred / validation required
- **Primary sources (committed):** docs/POSTGRESQL_PHYSICAL_SCHEMA_OPEN_DECISIONS.md; docs/POSTGRESQL_ROUND3_READINESS_AND_BLOCKER_MATRIX.md
- **Problem / unresolved question:** Measured workload/query/index/partition thresholds and validation evidence are not yet established.
- **Why a decision is needed:** Optimization/partitioning decisions without evidence can harm performance, operability, or correctness (e.g. uniqueness/key design).
- **Viable alternatives/options supported by source documents:** Sources defer partitioning/index refinement until measured thresholds; PD-010 and index strategy require validation (I-11/I-14).
- **Copilot analysis (not a source-backed decision or approval):** Copilot analysis (advisory): collect representative workload and growth profiles, validate query plans/index trade-offs (including write amplification), and require partition-key-inclusive uniqueness design if adopted.
- **Consequences / implications:** Impacts I-11 hardening and I-14 partitioning/maintenance; performance/operability sign-off.
- **Dependencies and affected increments:** OD-010, PD-001/008/009/010.
- **Risks if unresolved or incorrectly assumed:** Premature partitioning or indexing can increase complexity, maintenance burden, and regression risk.
- **Information gaps / owner clarification needed:** Requires DBA/operations evidence and thresholds; **validation gap**.
- **Blocking characterization:** **Deferrable validation prerequisite** (blocks optimization/automation sign-off).

### OD-013 — Connector-specific event identity namespace and fallback behavior for missing/unreliable upstream IDs
- **Recorded status (preserved):** Proposed (open/partial)
- **Primary sources (committed):** docs/POSTGRESQL_PHYSICAL_SCHEMA_OPEN_DECISIONS.md; docs/POSTGRESQL_ROUND3_READINESS_AND_BLOCKER_MATRIX.md
- **Problem / unresolved question:** Approved per-connector namespace and fallback dedup predicates for missing/unreliable upstream IDs remain open/partial.
- **Why a decision is needed:** Ingestion dedup correctness depends on explicit namespace/provenance and safe fallback semantics, distinct from identity/licensing idempotency.
- **Viable alternatives/options supported by source documents:** Source-backed constraints: `ingest.event_receipt` must carry explicit namespace/provenance; device-scoped upstream IDs must include stable source-device binding namespace in multi-device contexts; fallback fingerprint when missing/unreliable (as recorded in baselines). PD-008 proposes predicate implementation patterns pending approval.
- **Copilot analysis (not a source-backed decision or approval):** Copilot analysis (advisory): define per-connector canonical namespace keys and deterministic fallback fingerprint inputs/provenance markers; validate uniqueness predicates to avoid false merges/drops across sources.
- **Consequences / implications:** Impacts I-07 (Op 10), dedup integrity, downstream processing reliability.
- **Dependencies and affected increments:** PD-008; architecture/integration/operations/security.
- **Risks if unresolved or incorrectly assumed:** Incorrect dedup can drop legitimate events or admit duplicates, affecting detection/case timelines.
- **Information gaps / owner clarification needed:** Connector-specific specifications and approved predicates incomplete; **information gap/partial decision**.
- **Blocking characterization:** **Conditional prerequisite / partial hard blocker** for finalized ingest dedup behavior.

## 2. Physical-design decision briefs (PD-001–PD-012)

### PD-001 — UUID generation/version and ordering strategy for PKs and high-insert tables
- **Recorded status (preserved):** Proposed
- **Primary sources (committed):** docs/POSTGRESQL_PHYSICAL_SCHEMA_OPEN_DECISIONS.md
- **Problem / unresolved question:** Select UUID strategy balancing locality/bloat/write amplification and tooling support.
- **Why a decision is needed:** Impacts PK/index behavior across high-insert and related tables (I-01 conventions and dependent increments).
- **Viable alternatives/options supported by source documents:** Options considered (source): UUIDv4, UUIDv7/time-ordered, application-generated vs DB-generated. Proposed direction favors time-ordered app-generated IDs if supported, else UUIDv4 with measured impact.
- **Copilot analysis (not a source-backed decision or approval):** Copilot analysis (advisory): validate PostgreSQL/tooling/ORM support and index behavior under expected workloads before committing; do not assume performance gains without evidence (OD-012).
- **Consequences / implications:** Affects index locality, write amplification, operational characteristics.
- **Dependencies and affected increments:** OD-012; cross-cutting conventions (I-01).
- **Risks if unresolved or incorrectly assumed:** Poor fit can increase bloat/hotspots and maintenance cost.
- **Information gaps / owner clarification needed:** Requires engineering/DBA decision and workload validation.
- **Blocking characterization:** **Conditional prerequisite** (cross-cutting).

### PD-002 — State/type representation (enum vs constrained text+CHECK vs lookup tables)
- **Recorded status (preserved):** Proposed
- **Primary sources (committed):** docs/POSTGRESQL_PHYSICAL_SCHEMA_OPEN_DECISIONS.md
- **Problem / unresolved question:** Choose representation for evolving states and governed catalogs.
- **Why a decision is needed:** Affects migration flexibility, integrity clarity, and governance overhead (I-01+).
- **Viable alternatives/options supported by source documents:** Options considered (source): native enum, text+CHECK, lookup/reference tables. Proposed: constrained text+CHECK for evolving states initially; lookup tables for governed catalogs where valuable.
- **Copilot analysis (not a source-backed decision or approval):** Copilot analysis (advisory): prefer representations that support controlled evolution and clear integrity constraints; document transition/migration implications for any chosen option.
- **Consequences / implications:** Impacts schema evolution and validation logic.
- **Dependencies and affected increments:** I-01 conventions; domain modeling.
- **Risks if unresolved or incorrectly assumed:** Rigid choices can complicate migrations; loose choices can weaken integrity.
- **Information gaps / owner clarification needed:** Requires engineering/architecture review; no approved final choice.
- **Blocking characterization:** **Conditional prerequisite** (cross-cutting).

### PD-003 — Tenant-consistent referential enforcement pattern for surrogate-key relationships
- **Recorded status (preserved):** Proposed
- **Primary sources (committed):** docs/POSTGRESQL_PHYSICAL_SCHEMA_OPEN_DECISIONS.md; docs/POSTGRESQL_ROUND3_READINESS_AND_BLOCKER_MATRIX.md
- **Problem / unresolved question:** Prevent cross-tenant references through robust relational enforcement patterns.
- **Why a decision is needed:** Critical for tenant isolation integrity in data model (I-03+ and I-11).
- **Viable alternatives/options supported by source documents:** Options considered (source): single-column FK only, composite unique `(tenant_id,id)` + composite FK, trigger-based validation, mixed. Proposed: composite uniques/FKs for critical tenant-owned relationships where feasible, with documented exceptions/compensating controls.
- **Copilot analysis (not a source-backed decision or approval):** Copilot analysis (advisory): favor declarative tenant-consistent constraints on critical paths; if exceptions are necessary, require explicit compensating controls and security review.
- **Consequences / implications:** Directly impacts cross-tenant reference prevention and schema/index complexity.
- **Dependencies and affected increments:** Tenant isolation invariants; PD-005/PD-006 runtime controls complementary but not substitutes.
- **Risks if unresolved or incorrectly assumed:** Weak enforcement increases risk of cross-tenant data corruption/leakage.
- **Information gaps / owner clarification needed:** Implementation validation and security/DB design review required.
- **Blocking characterization:** **Conditional prerequisite / integrity control** (high impact).

### PD-004 — Physical materialization of `core.source_device_key` dependent projection
- **Recorded status (preserved):** Proposed (bounded)
- **Primary sources (committed):** docs/POSTGRESQL_PHYSICAL_SCHEMA_OPEN_DECISIONS.md
- **Problem / unresolved question:** Decide whether to materialize a dependent projection table without creating competing authority.
- **Why a decision is needed:** Affects identity schema simplicity and divergence risk (I-04).
- **Viable alternatives/options supported by source documents:** Options considered (source): materialized 1:1 table vs no separate table (binding-owned columns). Proposed: prefer binding-owned columns unless projection needed; if materialized enforce strict 1:1 non-authoritative parity.
- **Copilot analysis (not a source-backed decision or approval):** Copilot analysis (advisory): avoid redundant mutable state; any projection must be mechanically constrained to the authoritative binding (OD-002).
- **Consequences / implications:** Impacts maintainability and correctness of identity model.
- **Dependencies and affected increments:** OD-002.
- **Risks if unresolved or incorrectly assumed:** Projection divergence could undermine binding authority.
- **Information gaps / owner clarification needed:** Bounded proposal pending architecture/security review.
- **Blocking characterization:** **Conditional prerequisite** for I-04 finalization.

### PD-005 — Verified tenant-context database mechanism (within invariants)
- **Recorded status (preserved):** Proposed
- **Primary sources (committed):** docs/POSTGRESQL_PHYSICAL_SCHEMA_OPEN_DECISIONS.md; docs/POSTGRESQL_ROUND3_READINESS_AND_BLOCKER_MATRIX.md; docs/POSTGRESQL_ROUND3_FINAL_REVIEW.md
- **Problem / unresolved question:** Establish a safe, non-client-authoritative, non-GUC mechanism for verified transaction-bound tenant context usable by DB enforcement.
- **Why a decision is needed:** Essential for RLS correctness, pooling safety, and tenant-runtime authorization posture (I-12).
- **Viable alternatives/options supported by source documents:** Source-backed direction: trusted transaction-bound verified-context mechanism validated by hardened helpers/internal structures; never client-supplied tenant IDs or user-settable PostgreSQL GUC authorization. (Specific mechanism options not fully enumerated in committed baseline.)
- **Copilot analysis (not a source-backed decision or approval):** Copilot analysis (advisory): require threat-modeled, security-reviewed mechanism with connection-pool reset guarantees and negative tests; treat as hard gate before tenant-runtime exposure.
- **Consequences / implications:** Determines feasibility/safety of I-12 and any tenant-scoped runtime behavior.
- **Dependencies and affected increments:** PD-006, tenant isolation invariants, I-12.
- **Risks if unresolved or incorrectly assumed:** Bypass or context leakage can cause cross-tenant access.
- **Information gaps / owner clarification needed:** Mechanism details/validation evidence not available; **critical information/approval gap**.
- **Blocking characterization:** **Hard blocker** for I-12 and tenant-runtime safety.

### PD-006 — RLS FORCE behavior and table ownership hardening details
- **Recorded status (preserved):** Deferred
- **Primary sources (committed):** docs/POSTGRESQL_PHYSICAL_SCHEMA_OPEN_DECISIONS.md; docs/POSTGRESQL_ROUND3_READINESS_AND_BLOCKER_MATRIX.md
- **Problem / unresolved question:** Finalize RLS enable/FORCE applicability and ownership/role hardening compatible with controlled operations.
- **Why a decision is needed:** Affects bypass resistance and administrative operability (I-12).
- **Viable alternatives/options supported by source documents:** Source indicates enable RLS on tenant-protected tables and apply FORCE where compatible; exact applicability deferred to implementation review.
- **Copilot analysis (not a source-backed decision or approval):** Copilot analysis (advisory): minimize bypass paths, document/justify any controlled exceptions, and validate with privileged-role negative tests; align with PD-005 mechanism.
- **Consequences / implications:** Impacts defense-in-depth effectiveness and operations.
- **Dependencies and affected increments:** PD-005; security/DBA governance.
- **Risks if unresolved or incorrectly assumed:** Misconfiguration can permit unintended bypass or break controlled maintenance.
- **Information gaps / owner clarification needed:** Deferred; requires security/DBA review and environment-specific validation.
- **Blocking characterization:** **Hard blocker/deferred prerequisite** for I-12 finalization.

### PD-007 — Outbox claim mechanism and lease/fencing implementation details
- **Recorded status (preserved):** Proposed
- **Primary sources (committed):** docs/POSTGRESQL_PHYSICAL_SCHEMA_OPEN_DECISIONS.md; docs/POSTGRESQL_ROUND3_READINESS_AND_BLOCKER_MATRIX.md
- **Problem / unresolved question:** Select and validate a safe outbox claim/lease/fencing approach under at-least-once semantics.
- **Why a decision is needed:** Impacts throughput, contention, and duplicate-processing safety (I-08, Ops 11/12).
- **Viable alternatives/options supported by source documents:** Options considered (source): `FOR UPDATE SKIP LOCKED` claim, advisory locks, lease-token CAS updates, hybrid. Proposed: DB-row claim with lease token/expiry/heartbeat and atomic transitions; `SKIP LOCKED` likely suitable but must be validated.
- **Copilot analysis (not a source-backed decision or approval):** Copilot analysis (advisory): validate under contention/failure/restart scenarios and ensure fencing prevents stale workers from committing conflicting state; preserve unknown-outcome handling (OD-009).
- **Consequences / implications:** Affects reliability and operational behavior of outbox processing.
- **Dependencies and affected increments:** OD-009, OD-012.
- **Risks if unresolved or incorrectly assumed:** Race conditions or weak fencing can duplicate or lose processing effects.
- **Information gaps / owner clarification needed:** Requires engineering validation and approved semantics.
- **Blocking characterization:** **Conditional prerequisite** for I-08/runtime behavior.

### PD-008 — Event receipt dedup uniqueness predicate finalization per connector/namespace
- **Recorded status (preserved):** Proposed
- **Primary sources (committed):** docs/POSTGRESQL_PHYSICAL_SCHEMA_OPEN_DECISIONS.md; docs/POSTGRESQL_ROUND3_READINESS_AND_BLOCKER_MATRIX.md
- **Problem / unresolved question:** Define correct uniqueness predicates for event receipt dedup across namespaces/fallback cases.
- **Why a decision is needed:** Impacts ingest correctness and write/index cost (I-07, Op 10).
- **Viable alternatives/options supported by source documents:** Options considered (source): single global unique, multiple partial uniques by namespace/id basis, generated canonical key column. Proposed: multiple explicit partial/conditional unique indexes matching approved namespace semantics and fallback rules.
- **Copilot analysis (not a source-backed decision or approval):** Copilot analysis (advisory): align predicates exactly with approved OD-013 namespace/provenance rules and test collision/ambiguity cases; keep distinct from identity/licensing ledger.
- **Consequences / implications:** Affects dedup correctness and downstream processing.
- **Dependencies and affected increments:** OD-013.
- **Risks if unresolved or incorrectly assumed:** Overly broad/narrow predicates can drop or duplicate events.
- **Information gaps / owner clarification needed:** Depends on OD-013 connector-specific decisions; **information gap**.
- **Blocking characterization:** **Conditional prerequisite** for I-07 finalization.

### PD-009 — JSONB indexing policy for operational/SOC/inventory attributes
- **Recorded status (preserved):** Proposed
- **Primary sources (committed):** docs/POSTGRESQL_PHYSICAL_SCHEMA_OPEN_DECISIONS.md; docs/POSTGRESQL_ROUND3_READINESS_AND_BLOCKER_MATRIX.md
- **Problem / unresolved question:** Control JSONB indexing to balance query needs with write/storage/maintenance and sensitivity concerns.
- **Why a decision is needed:** Impacts I-10/I-11 performance and exposure posture.
- **Viable alternatives/options supported by source documents:** Options considered (source): no JSONB indexes, selective expression indexes, targeted GIN indexes. Proposed: no default GIN; add selective indexes only for proven query paths with sensitivity review.
- **Copilot analysis (not a source-backed decision or approval):** Copilot analysis (advisory): require measured query-path justification and review indexed paths for sensitive data exposure; prefer targeted expression indexes where sufficient.
- **Consequences / implications:** Affects query flexibility, cost, and risk.
- **Dependencies and affected increments:** OD-012.
- **Risks if unresolved or incorrectly assumed:** Unvalidated GIN/indexing can degrade writes and broaden exposure.
- **Information gaps / owner clarification needed:** Requires workload evidence and security/DBA validation.
- **Blocking characterization:** **Conditional/deferrable validation prerequisite**.

### PD-010 — Partitioning adoption triggers and initial partition keys
- **Recorded status (preserved):** Deferred
- **Primary sources (committed):** docs/POSTGRESQL_PHYSICAL_SCHEMA_OPEN_DECISIONS.md; docs/POSTGRESQL_ROUND3_READINESS_AND_BLOCKER_MATRIX.md
- **Problem / unresolved question:** Adopt partitioning only when justified by evidence and compatible with constraints/lifecycle governance.
- **Why a decision is needed:** Impacts operability, migration complexity, and lifecycle automation (I-14).
- **Viable alternatives/options supported by source documents:** Options considered (source): no partitioning now, immediate partitioning, threshold-based deferred adoption. Proposed: defer; adopt only after measured thresholds with partition-key-inclusive uniqueness design.
- **Copilot analysis (not a source-backed decision or approval):** Copilot analysis (advisory): validate retention/legal-hold behavior, uniqueness/FK implications, and maintenance tooling before adoption; avoid premature partitioning.
- **Consequences / implications:** Affects long-term operations and performance.
- **Dependencies and affected increments:** OD-010, OD-012.
- **Risks if unresolved or incorrectly assumed:** Premature or incompatible partitioning can break constraints/operations.
- **Information gaps / owner clarification needed:** Deferred pending evidence and governance approvals.
- **Blocking characterization:** **Deferrable prerequisite** (blocks I-14 adoption).

### PD-011 — Cryptographic/hash representation for evidence and fingerprint-protection artifacts
- **Recorded status (preserved):** Proposed
- **Primary sources (committed):** docs/POSTGRESQL_PHYSICAL_SCHEMA_OPEN_DECISIONS.md
- **Problem / unresolved question:** Standardize representation for integrity/fingerprint artifacts to support verification and interoperability.
- **Why a decision is needed:** Impacts evidence integrity tooling and fingerprint-related storage (I-04, I-09).
- **Viable alternatives/options supported by source documents:** Options considered (source): `text` encoding, `bytea`, algorithm metadata columns. Proposed: store algorithm identifier plus hash/derived value in consistent encoded form; exact type chosen for interoperability/indexing needs.
- **Copilot analysis (not a source-backed decision or approval):** Copilot analysis (advisory): include algorithm/version metadata and ensure constant, verifiable encoding/handling practices aligned with OD-006/OD-010 requirements.
- **Consequences / implications:** Affects verification, storage, and future migrations.
- **Dependencies and affected increments:** OD-006, OD-010.
- **Risks if unresolved or incorrectly assumed:** Inconsistent representation complicates verification and rotation/migration.
- **Information gaps / owner clarification needed:** Requires security/engineering review and policy alignment.
- **Blocking characterization:** **Conditional prerequisite**.

### PD-012 — Physical handling of global-vs-tenant detection rules and platform-level audit rows
- **Recorded status (preserved):** Proposed
- **Primary sources (committed):** docs/POSTGRESQL_PHYSICAL_SCHEMA_OPEN_DECISIONS.md; docs/POSTGRESQL_ROUND3_READINESS_AND_BLOCKER_MATRIX.md
- **Problem / unresolved question:** Model global vs tenant scope explicitly to prevent leakage while supporting governed platform/admin needs.
- **Why a decision is needed:** Impacts isolation clarity and access governance (I-02, I-10).
- **Viable alternatives/options supported by source documents:** Options considered (source): strict tenant-only tables, nullable-scope tables with guarded access, separate global tables. Proposed: prefer explicit scope modeling and separate global catalog tables where truly global; guarded access for any admin/global rows.
- **Copilot analysis (not a source-backed decision or approval):** Copilot analysis (advisory): minimize nullable-scope ambiguity, enforce strict access paths/policies, and test cross-tenant leakage cases; align with support-access/audit governance constraints.
- **Consequences / implications:** Affects leakage risk and administrative flexibility.
- **Dependencies and affected increments:** Tenant isolation invariants; OD-010 (controlled admin implications).
- **Risks if unresolved or incorrectly assumed:** Ambiguous scope modeling can create privilege or data-leakage paths.
- **Information gaps / owner clarification needed:** Requires security/architecture review and validation.
- **Blocking characterization:** **Conditional prerequisite** for scope-sensitive structures.
