# CARES PostgreSQL Round 3.2 — Owner Decision Register (Consolidated, Round 3.2.1 Fidelity-Corrected)

**Status:** Proposed governance consolidation record only; **NOT IMPLEMENTED, NOT TESTED, NOT AN IMPLEMENTATION AUTHORIZATION**.  
**Round:** Round 3.2 — Owner Decision Consolidation and Governance Reconciliation; **Round 3.2.1 — Owner Decision Fidelity Correction** (documentation/governance only).  
**Verified source branch/baseline:** `governance/postgresql-round3-2-owner-decision-consolidation` @ `cd950882b0ea0e58781d9ba8f10440bd383f9b58` (local and remote verified; clean source worktree; expected Round 3.2 deliverables present).  
**Working branch:** `governance/postgresql-round3-2-1-owner-decision-fidelity-correction` (created from the verified source commit in isolated worktree `/tmp/cares-postgresql-round3-2-1`; source branch unchanged).

## 1. Purpose and authoritative input

This register is the authoritative Round 3.2 consolidated record for **OD-001 through OD-013**, corrected in **Round 3.2.1** to ensure the published governance documents accurately and completely reflect the owner’s **explicitly approved principles and bounded conditions** as provided in the Round 3.2.1 implementation prompt (authoritative owner decisions).

**Authoritative sources consulted/reconciled (read-only evidence where applicable):**
- Explicit owner-approved principles and bounded conditions for OD-001–OD-013 (Round 3.2.1 prompt, authoritative decision input).
- Round 3.2 baseline artifacts on `cd950882...`: [POSTGRESQL_ROUND3_2_OWNER_DECISION_REGISTER.md](./POSTGRESQL_ROUND3_2_OWNER_DECISION_REGISTER.md) (prior), [POSTGRESQL_ROUND3_2_IMPLEMENTATION_AUTHORIZATION_MATRIX.md](./POSTGRESQL_ROUND3_2_IMPLEMENTATION_AUTHORIZATION_MATRIX.md), [POSTGRESQL_ROUND3_2_DEPENDENCY_AND_BLOCKER_MAP.md](./POSTGRESQL_ROUND3_2_DEPENDENCY_AND_BLOCKER_MAP.md), [POSTGRESQL_ROUND3_2_FINAL_REVIEW.md](./POSTGRESQL_ROUND3_2_FINAL_REVIEW.md), [POSTGRESQL_ROUND3_2_CHANGELOG.md](./POSTGRESQL_ROUND3_2_CHANGELOG.md), [adr/0006-atomic-per-tenant-asset-licensing.md](./adr/0006-atomic-per-tenant-asset-licensing.md).
- Round 3.1 governance artifacts (`POSTGRESQL_ROUND3_1_*`) and Round 3 planning/readiness/dependency/final-review/changelog/publication-audit records.
- Committed Round 1.1/Round 2 records, including [POSTGRESQL_PHYSICAL_SCHEMA_OPEN_DECISIONS.md](./POSTGRESQL_PHYSICAL_SCHEMA_OPEN_DECISIONS.md) (PD-001–PD-012 preserved).
- Recovered original sources (provenance limitation preserved): `docs/POSTGRESQL_SCHEMA_OPEN_DECISIONS.md` (blob `dc9a813be82bfa6ba1384b404d3805b67f2be88c`, 61 lines, recovered from agent checkpoint commit `278daf4623404f573132cee57e1d6fbe33b0846d`; provenance `FOUND BUT PROVENANCE INCOMPLETE`, not claimed present in published Round 3 baseline/public lineage) and [adr/0006-atomic-per-tenant-asset-licensing.md](./adr/0006-atomic-per-tenant-asset-licensing.md) baseline content (blob `324a6eedcf7da9ced1294cc48a832e2c56bad99f`, 274 lines, **Status: Proposed**, recovered from agent checkpoint history; same provenance limitation).

**No invention / no reinterpretation rule:** this correction preserves the meaning and all bounded conditions of the owner’s explicitly approved principles. It does **not** reinterpret, weaken, expand, or replace owner decisions; does **not** invent decisions or technical details not approved; does **not** mark an OD fully technically specified merely because governing principles are approved; and does **not** convert principle approval, conditional readiness, or planning recommendations into implementation permission or authorization.

## 2. Preserved baselines and global constraints

| Baseline | Status preserved |
|---|---|
| OD-001–OD-013 identifiers | Preserved and traceable. |
| PD-001–PD-012 identifiers/statuses | Preserved as recorded in [POSTGRESQL_PHYSICAL_SCHEMA_OPEN_DECISIONS.md](./POSTGRESQL_PHYSICAL_SCHEMA_OPEN_DECISIONS.md) and Round 3/3.1 records (**unresolved/deferred where applicable; not closed by OD-001–OD-013 principle approvals**). |
| ADR 0006 | **Formal ADR status remains Proposed.** OD-001 records **acceptance in principle with bounded conditions/dependencies**; this is **not** unconditional formal ADR acceptance. No status change to Accepted/Approved/final unless a separate formal ADR governance action explicitly provides it (none provided). |
| I-00–I-14 boundaries | Preserved; dependencies reconciled without silently widening scope. **No implementation increment authorized** (including I-06, I-07, I-09, I-12, I-13, I-14). |

**Mandatory invariants preserved:** Python backend; PostgreSQL primary system of record; modular monolith; core functional without MELIRA; MELIRA external SaaS only (explicit provider/model/region, no silent failover, no automatic transfer, no local inference, no local GPU); one unique monitored device = one licensed asset per tenant (multi-source same-device no duplicate licensing; equal device-type weight); strict multi-tenancy with tenant authority only from trusted, verified, transaction-bound context (**never** client-supplied tenant IDs, **never** user-settable PostgreSQL GUC authorization), RLS defense-in-depth not sufficient alone. No DDL/migrations/ORM/DB provisioning/roles/policies/triggers/functions/runtime implementation or implementation authorization granted.

## 3. OD-001–OD-013 consolidated fidelity register

For each OD: **owner-approved principle**, **bounded conditions and prohibitions**, **deferred technical details**, **dependencies on other decisions**, **implementation authorization status**, **related implementation increments (where applicable)**, and **whether any unresolved detail remains a blocker** are explicitly stated.

### OD-001 — ADR 0006 / per-tenant asset licensing (acceptance in principle, bounded)

- **Owner-approved principle:** The owner approved **ADR 0006 in principle**, subject to the previously specified bounded conditions. ADR 0006 concerns **atomic per-tenant asset licensing/accounting of monitored devices**; it is **not** the CARES software subscription license.
- **Bounded conditions and prohibitions (preserved):**
  - One unique monitored device represents exactly **one licensed asset per tenant**.
  - Multiple reporting sources for the same device must **not** double-count it.
  - All device types have **equal licensing weight**; do **not** introduce OS-, vendor-, device-type-, or telemetry-volume-based weighting.
  - Asset licensing remains **separate** from technical resource quotas.
  - Preserve dependencies on **OD-003, OD-004, and OD-008**.
  - Do **not** represent the owner’s approval in principle as unconditional formal ADR acceptance.
  - Keep **ADR 0006 status Proposed** unless a separate formal ADR governance action explicitly changes it.
  - Approval in principle does **not** authorize implementation.
- **Deferred technical details (explicitly not approved/finalized):** reservation policy details (OD-003 linkage), accounting/counter/reconciliation mechanics and edge cases (OD-004 linkage), merge/split accounting edge cases and lifecycle details, formal idempotency contract/coupling/canonicalization details (OD-008), schema-level interpretation finalization, and any formal schema/security/architecture review/acceptance record required for unconditional status transition.
- **Dependencies on other decisions:** ADR 0006 (Proposed), OD-003, OD-004, OD-008; related OD-002/OD-005 and PD-001/PD-003/PD-004/PD-005/PD-006 as applicable to licensing/accounting enforcement context.
- **Implementation authorization status:** **Not authorized.** No implementation increment authorized by this approval.
- **Related implementation increments (where applicable):** I-06 (final semantics/structures), I-12, I-13, I-14 (as affected by licensing/correctness/isolation prerequisites); none authorized.
- **Unresolved detail remains a blocker:** **Yes.** Technical details, validations, formal ADR governance/acceptance requirements (for unconditional transition), and separate explicit authorization remain unresolved/required.

### OD-002 — Authoritative asset binding

- **Owner-approved principle:** `core.asset_data_source` is the **sole authoritative owner** of the stable source-device binding. `source_device_key_id` is **immutable** throughout the binding lifecycle.
- **Bounded conditions and prohibitions (preserved):**
  - Do **not** create `core.source_device_key` in the initial implementation.
  - If a separate `source_device_key` representation is ever justified, it may only be a **dependent, one-to-one, non-authoritative projection** with the **same lifecycle**.
  - Raw source identifiers and fingerprint aliases **cannot replace** the authoritative binding.
  - Fingerprints are **supporting evidence, not authoritative identity**.
  - Fingerprint protection and rotation remain subject to **OD-006**.
  - Reinstall and re-enrollment lifecycle remains subject to **OD-007**.
  - Connector-specific uniqueness remains subject to **OD-013**.
  - Do **not** convert this approval into permission to implement the binding.
- **Deferred technical details (explicitly not approved/finalized):** final physical PK/FK/uniqueness/authority/join-path/materialization decisions and validations; dependent projection materialization details (PD-004 linkage); fingerprint protection/rotation/custody implementation (OD-006); reinstall/re-enrollment protocol/mechanics (OD-007); connector-specific uniqueness/predicate details (OD-013); schema/security validation evidence.
- **Dependencies on other decisions:** OD-006, OD-007, OD-013; related OD-001/OD-008 and PD-003/PD-004/PD-011.
- **Implementation authorization status:** **Not authorized.** No implementation increment authorized.
- **Related implementation increments (where applicable):** I-04, I-05, I-06, I-07, I-13 (none authorized).
- **Unresolved detail remains a blocker:** **Yes.** Technical design/finalization, validation, and separate explicit authorization remain required.

### OD-003 — Pending asset reservation

- **Owner-approved principle:** The owner approved the **principle of pending asset reservation**, subject to bounded conditions.
- **Bounded conditions and prohibitions (preserved):**
  - A pending reservation is **not yet** a committed licensed asset.
  - Reservation must **not** be confused with final asset activation or committed licensing accounting.
  - The design must prevent concurrent operations from creating **oversubscription or double-counting**.
  - Preserve dependencies on **OD-004 and OD-001**.
  - Do **not** invent reservation durations, state transitions, or implementation mechanics that have not been approved.
- **Deferred technical details (explicitly not approved/finalized):** exact reservation lifecycle, expiration, recovery, concurrency, and accounting mechanics; duration/timeout/release/representation; policy-to-schema/state mapping and operational workflow details.
- **Dependencies on other decisions:** OD-001, OD-004 (and OD-008 as applicable for correctness/idempotency).
- **Implementation authorization status:** **Not authorized.** No implementation increment authorized.
- **Related implementation increments (where applicable):** I-06, I-13 (none authorized).
- **Unresolved detail remains a blocker:** **Yes.** Policy/technical details, validation, and separate explicit authorization remain required.

### OD-004 — Accounting counter and reconciliation

- **Owner-approved principle:** The owner approved the **principles of accounting counters and reconciliation**, subject to bounded conditions.
- **Bounded conditions and prohibitions (preserved):**
  - **Atomicity** of licensing-related accounting.
  - Protection against **double-counting and oversubscription**.
  - Reconciliation as a way to **detect and correct counter drift**.
  - Clear distinction between **committed licensed assets** and **pending reservations**.
  - Preserve dependencies on **OD-001, OD-003, and OD-008**.
  - Do **not** invent numerical limits or operational policies.
- **Deferred technical details (explicitly not approved/finalized):** exact counter-maintenance mechanisms, reconciliation scheduling, repair behavior, locking strategy, edge cases, authoritative counter scope, equations/formulas, and state-to-counter mapping details.
- **Dependencies on other decisions:** OD-001, OD-003, OD-008 (and related OD-005 as applicable).
- **Implementation authorization status:** **Not authorized.** No implementation increment authorized.
- **Related implementation increments (where applicable):** I-06, I-13, I-14 (none authorized).
- **Unresolved detail remains a blocker:** **Yes.** Technical/accounting details, validation, and separate explicit authorization remain required.

### OD-005 — Asset merge and split

- **Owner-approved principle:** The owner approved the **principles of asset merge and split**, subject to bounded conditions.
- **Bounded conditions and prohibitions (preserved):**
  - **Asset lineage and historical relationships** must be preserved.
  - **Typed, relationally enforceable lineage relationships** rather than an untyped polymorphic reference.
  - **Explicit authorization and auditability** for merge/split operations.
  - **Licensing accounting consequences** must be handled consistently.
  - **Historical evidence and provenance** must not silently disappear.
  - Do **not** imply that merge or split can be performed implicitly or without authorization.
- **Deferred technical details (explicitly not approved/finalized):** technical edge cases, detailed transition rules, accounting implementation, authority/evidence/workflow specifics, and execution semantics.
- **Dependencies on other decisions:** OD-001/OD-004/OD-006/OD-007/OD-008 (and PD-004/PD-011 as applicable).
- **Implementation authorization status:** **Not authorized.** No implementation increment authorized.
- **Related implementation increments (where applicable):** I-05, I-06, I-13 (none authorized).
- **Unresolved detail remains a blocker:** **Yes.** Governance/technical details, validation, and separate explicit authorization remain required.

### OD-006 — Fingerprint protection and key custody

- **Owner-approved principle:** Fingerprints are **supporting evidence, not authoritative identity**. Use a **keyed cryptographic construction** for protected fingerprinting. The key must be managed **outside the database**. Key rotation must **not** break historical identity continuity or authoritative asset binding.
- **Bounded conditions and prohibitions (preserved):**
  - A fingerprint alone is **insufficient** to authorize an asset merge.
  - Raw identifiers and fingerprint aliases must **not** displace the authoritative source-device binding.
  - Do **not** select or claim owner approval for a specific algorithm or KMS.
- **Deferred technical details (explicitly not approved/finalized):** exact algorithm, key-management service, rotation procedure, versioning mechanics, operational key-custody implementation, overlap duration, and re-fingerprinting migration process.
- **Dependencies on other decisions:** OD-002 (authoritative binding), OD-007 (re-enrollment/lifecycle context), OD-001/OD-008 (identity/licensing correctness context); related PD-004/PD-011.
- **Implementation authorization status:** **Not authorized.** No implementation increment authorized.
- **Related implementation increments (where applicable):** I-04, I-13 (none authorized).
- **Unresolved detail remains a blocker:** **Yes.** Security/crypto/platform decisions, validation, and separate explicit authorization remain required.

### OD-007 — Agent reinstall and re-enrollment lifecycle

- **Owner-approved principle:** The owner approved all of the following (preserved in full):
  1. Asset identity, source-device binding, agent installation identity, and agent credential are **distinct concepts**.
  2. Reinstalling an agent does **not automatically** create a new licensed asset.
  3. Rotating an agent credential does **not automatically** create a new licensed asset.
  4. Re-enrollment of the same physical/logical device requires **continuity verification**.
  5. Old credentials may be revoked and are **not automatically inherited** by a new installation.
  6. Cloned devices must **not automatically** be treated as the same device.
  7. An authoritative source-device binding **cannot change implicitly**.
  8. Enrollment must be **authorized and auditable**, with **replay protection**.
  9. Cross-tenant transfer requires an **explicit lifecycle transition**.
  10. Credential continuity must **not** be assumed merely because identifiers or fingerprints appear similar.
- **Bounded conditions and prohibitions (preserved):** Do **not** simplify this decision to “reinstall preserves identity” without the required continuity verification and authorization controls.
- **Deferred technical details (explicitly not approved/finalized):** enrollment protocol, continuity algorithms, credential issuance and revocation mechanics, replay-protection implementation, retirement policy, and operational conflict-handling procedures.
- **Dependencies on other decisions:** OD-002, OD-005, OD-006, OD-008; related PD-004.
- **Implementation authorization status:** **Not authorized.** No implementation increment authorized.
- **Related implementation increments (where applicable):** I-04, I-05 (none authorized).
- **Unresolved detail remains a blocker:** **Yes.** Lifecycle/protocol/mechanics decisions, validation, and separate explicit authorization remain required.

### OD-008 — Idempotency contract

- **Owner-approved principle:** Idempotency for identity/licensing/correctness-critical operations must be durable and retry-safe with deterministic canonicalization and no duplicate business effects under approved semantics.
- **Bounded conditions and prohibitions (preserved):**
  - **Scope and uniqueness:** unique idempotency scope is **`(tenant_id, operation_type, idempotency_key)`**. The request must have a **deterministic, versioned canonical representation**. A **deterministic request hash** is derived from that canonical representation.
  - **Replay and conflict behavior:** same scope, same key, same request hash → **replay the prior result without producing a duplicate business effect**. Same scope and key but different request hash → **return a terminal conflict and do not perform a second mutation**. Idempotency must be **durable enough** to support the defined retry and reconciliation horizon.
  - **Ledger states:** durable ledger states are **`in_progress`**, **`committed`**, **`failed_terminal`**. **`timeout_unknown_commit` is a caller-side unknown-outcome condition in the default single-transaction model; it is not automatically a durable ledger state in that model.**
  - **Transaction model:** **single-transaction coupling is the default** for database-local operations. **Staged or multi-transaction tracking is permitted only when a demonstrated need exists and separate approval is obtained.** Do **not** introduce staged processing as an assumed default.
  - **Retention and boundaries:** retention must align with the retry horizon and reconciliation requirements; **exact duration remains deferred**. Event receipt deduplication is **separate and governed by OD-013**. External delivery is **at-least-once**; do **not** claim exactly-once external delivery.
  - This approval does **not** authorize **I-06**, **I-13**, or implementation generally.
- **Deferred technical details (explicitly not approved/finalized):** covered operation-scope finalization, canonicalization/hash standard details, state-machine/terminal-rule details beyond approved states/semantics, retention duration, reconciliation workflow specifics, staged-tracking exception approvals/implementation details (leases/fencing if applicable), and timeout/unknown-commit operational contract details.
- **Dependencies on other decisions:** OD-001, OD-002, OD-003, OD-004, OD-005, OD-009, OD-010, OD-011, OD-013 (as applicable by operation/domain); ADR 0006; related PD-007.
- **Implementation authorization status:** **Not authorized.** No implementation increment authorized.
- **Related implementation increments (where applicable):** I-06, I-08, I-13 (none authorized).
- **Unresolved detail remains a blocker:** **Yes.** Formal contract/technical details, validations, and separate explicit authorization remain required.

### OD-009 — Outbox fencing, replay, and delivery uncertainty

- **Owner-approved principle:** Business-state/outbox consistency and safe at-least-once processing with explicit delivery uncertainty and replay/reconciliation separation.
- **Bounded conditions and prohibitions (preserved):**
  1. Business state changes and their corresponding outbox messages are created in the **same PostgreSQL transaction**.
  2. Outbox workers use **leases and fencing** for internal state transitions.
  3. A worker holding an **obsolete fencing token must not** be able to update internal outbox state.
  4. Lease expiry does **not** prove that external delivery failed.
  5. **`delivery_unknown`** must be represented as an **explicit delivery-uncertainty condition**.
  6. External delivery is **at-least-once** and may produce duplicates. Do **not** claim exactly-once delivery.
  7. Logical message identity remains **stable** across retries and replays.
  8. Each delivery attempt has its **own identity, status, and audit trail**.
  9. **Retry, replay, and reconciliation are separate operations.**
  - This approval does **not** authorize **I-09**, **I-13**, or implementation.
- **Deferred technical details (explicitly not approved/finalized):** lease duration and renewal, fencing implementation details, retry/backoff policy, dead-letter behavior, reconciliation procedure, connector-specific idempotency, manual replay authorization, payload retention and redaction, throughput/monitoring/operational thresholds.
- **Dependencies on other decisions:** OD-008, OD-012; related PD-007.
- **Implementation authorization status:** **Not authorized.** No implementation increment authorized.
- **Related implementation increments (where applicable):** I-08, I-09 (governance/structure linkage as applicable), I-13 (none authorized).
- **Unresolved detail remains a blocker:** **Yes.** Runtime semantics/mechanics, validation, and separate explicit authorization remain required.

### OD-010 — Evidence retention, legal hold, and deletion

- **Owner-approved principle:** Governed, auditable evidence lifecycle preserving integrity/provenance and preventing silent loss, with retention/legal-hold/deletion controls distinct from asset lifecycle.
- **Bounded conditions and prohibitions (preserved):**
  - Evidence **integrity, provenance, and auditability** must be preserved.
  - Corrections must **not** silently overwrite or erase historical evidence.
  - Retention must be based on **data category, purpose, and operational need**.
  - Legal hold must have a **defined scope, reason, authorization, audit trail, and review process**.
  - A legal hold **prevents automated deletion** within its applicable scope.
  - Deletion must check **retention obligations, legal holds, dependencies, and ownership**.
  - Deletion scope must include **derived data and copies that remain under CARES control**.
  - **Backup and external-copy limitations must be transparent.**
  - Deletion must be **idempotent, resumable, and verifiable**.
  - **Asset lifecycle and evidence lifecycle are separate.**
  - An **asset tombstone is not a justification** for retaining raw evidence indefinitely.
  - Do **not** invent retention periods or promise deletion from systems outside CARES control.
- **Deferred technical details (explicitly not approved/finalized):** exact retention durations, approval matrix, backup expiry and deletion mechanics, cryptographic erasure, WORM requirements, external deletion guarantees, regulatory mapping, AI-provider retention details.
- **Dependencies on other decisions:** OD-011, OD-012 (and governance linkages to controlled admin/access as applicable).
- **Implementation authorization status:** **Not authorized.** No implementation increment authorized.
- **Related implementation increments (where applicable):** I-09, I-14 (none authorized).
- **Unresolved detail remains a blocker:** **Yes.** Legal/privacy/security/compliance policy details, validation, and separate explicit authorization remain required.

### OD-011 — AI consent, data classification, budget, and provider policy

- **Owner-approved principle:** MELIRA/AI is optional, explicitly governed, auditable, and isolated from core operation and asset licensing, with fail-safe/minimization controls.
- **Bounded conditions and prohibitions (preserved):**
  - **Optional AI and consent:** MELIRA is **optional**. MELIRA requires **explicit tenant opt-in**. CARES core functionality must work **without MELIRA**. Consent must be **traceable and revocable**.
  - **Data eligibility and protection:** data classification determines whether data is eligible for AI processing. **Unclassified data must not** be sent to an AI provider. **Credentials, private keys, authentication secrets, and equivalent sensitive secrets are prohibited** from being sent to AI providers. **Data minimization and sanitization** must occur before provider transmission.
  - **Provider selection:** provider, model, region, and endpoint are **explicitly selected/configured per tenant**. **No silent failover** to a different provider, model, region, or endpoint. Provider selection must remain **transparent and auditable**.
  - **Budget and output:** AI budget is **separate from asset licensing**. AI budget enforcement must be **concurrency-safe**. AI outputs carry **provenance** and must **not** be represented as independently verified facts. AI recommendations do **not** authorize SOAR execution.
  - **Retention:** AI retention and deletion must align with **OD-010**. Provider-side limitations must be **transparent**.
  - This approval does **not** authorize implementation.
- **Deferred technical details (explicitly not approved/finalized):** consent schema, provider/model allowlist, region and endpoint controls, data-classification taxonomy, sanitization implementation, budget/pricing model, retention durations, DPA and contractual requirements, model-change process, evaluation and monitoring.
- **Dependencies on other decisions:** OD-010, OD-012.
- **Implementation authorization status:** **Not authorized.** No implementation increment authorized.
- **Related implementation increments (where applicable):** I-09 (none authorized).
- **Unresolved detail remains a blocker:** **Yes.** Policy/legal/security/commercial/technical details, validation, and separate explicit authorization remain required.

### OD-012 — Retention and workload validation

- **Owner-approved principle:** Evidence/governance-driven retention and workload validation preserving PostgreSQL/modular-monolith baseline and measurement-based decisions.
- **Bounded conditions and prohibitions (preserved):**
  - Retention must be based on **data category, purpose, and operational need**, consistent with **OD-010**.
  - Workload validation must cover **normal operation, bursts, concurrency, noisy tenants, recovery, retention, and reporting**.
  - **PostgreSQL remains the initial transactional database.** **Modular monolith remains the initial architecture.**
  - Indexing, partitioning, and optimization decisions must be **based on measurement**.
  - Additional technologies must only be introduced when **demonstrated necessary**.
  - **Asset licensing is separate from technical resource quotas.**
  - Overload and capacity exhaustion must be **explicit and auditable**.
  - Production readiness requires **benchmark, tenant-isolation, recovery, and retention testing**.
  - Do **not** turn this approval into authorization for implementation or a roadmap change.
- **Deferred technical details (explicitly not approved/finalized):** EPS targets, tenant and asset scale targets, retention duration, storage sizing, final partitioning and index strategy, SLO/SLA, RPO/RTO, quota thresholds, benchmark environment and datasets, scale-out decisions.
- **Dependencies on other decisions:** OD-010 (retention consistency), OD-009/OD-011/OD-013 (as applicable to workload/correctness/lifecycle contexts).
- **Implementation authorization status:** **Not authorized.** No implementation increment authorized.
- **Related implementation increments (where applicable):** I-10, I-11, I-14 (none authorized).
- **Unresolved detail remains a blocker:** **Yes.** Measured evidence, governance approvals, validation, and separate explicit authorization remain required.

### OD-013 — Event receipt deduplication namespace

- **Owner-approved principle:** Explicit, provenance-aware, namespace-scoped event receipt deduplication distinct from OD-008 identity/licensing idempotency.
- **Bounded conditions and prohibitions (preserved):**
  1. Every event receipt must carry **explicit namespace and provenance**.
  2. Namespace dimensions include **tenant, namespace type, namespace ID, and event identity**.
  3. Distinguish **data-source-global** upstream event IDs from **device-scoped** upstream event IDs.
  4. Device-scoped event IDs must use the **stable source-device binding** governed by **OD-002**.
  5. A data-source-global event ID may use `data_source_id` **only when** the connector guarantees uniqueness at that data-source level.
  6. Missing or unreliable upstream event IDs may use a **deterministic fallback fingerprint defined per connector**.
  7. Fallback fingerprints must be **versioned, canonical, and record the identity basis used**.
  8. There is **no universal fingerprint formula** for all connectors.
  9. If no reliable deduplication identity exists, **accept the event with an internal receipt identity and make no upstream deduplication claim**.
  10. Do **not** discard an event merely because its fingerprint is ambiguous or similar to another event. Duplicates may be handled by later correlation.
  11. **PD-008** unique predicates must follow these approved namespace semantics.
  12. Event receipt deduplication is **separate from OD-008** identity/licensing idempotency.
  - This approval does **not** authorize **I-07**.
- **Deferred technical details (explicitly not approved/finalized):** connector-specific identity rules, fallback formulas, final unique predicates, connector capability classification, payload-hash conflict policy details, and pre-binding/unresolved namespace derivation details.
- **Dependencies on other decisions:** OD-002, OD-008, OD-012; PD-008.
- **Implementation authorization status:** **Not authorized.** No implementation increment authorized.
- **Related implementation increments (where applicable):** I-07, I-11 (none authorized).
- **Unresolved detail remains a blocker:** **Yes.** Connector-specific decisions/predicates, validation, and separate explicit authorization remain required.

## 4. PD-001–PD-012 visibility (preserved, unresolved/deferred)

**PD-001 through PD-012 remain unresolved/deferred wherever recorded as such in the baseline.** Approval of OD-001–OD-013 principles/bounded conditions **does not automatically close** PD-001–PD-012. No PD is resolved by this consolidation.

| PD | Recorded status (preserved) | Reconciliation note |
|---|---|---|
| PD-001 | Proposed | UUID generation/ordering strategy remains technically unresolved pending approval/validation. |
| PD-002 | Proposed | State/type representation remains unresolved pending design review/migration considerations. |
| PD-003 | Proposed | Tenant-consistent referential enforcement pattern remains unresolved pending security/DB design validation. |
| PD-004 | Proposed (bounded) | `source_device_key` dependent projection/materialization remains unresolved pending OD-002-aligned approval/validation; no `core.source_device_key` in initial implementation per OD-002. |
| PD-005 | Proposed | Verified tenant-context DB mechanism remains a hard prerequisite; requires security/DBA approval and negative/pooling-reset validation. |
| PD-006 | Deferred | RLS FORCE/ownership hardening applicability remains deferred to reviewed implementation validation. |
| PD-007 | Proposed | Outbox claim/lease/fencing mechanism remains unresolved pending OD-009 semantics and validation. |
| PD-008 | Proposed | Event receipt dedup uniqueness predicates remain unresolved pending OD-013 connector-specific decisions and approved namespace semantics. |
| PD-009 | Proposed | JSONB indexing policy remains unresolved pending workload evidence and sensitivity review. |
| PD-010 | Deferred | Partitioning adoption/keys remain deferred pending thresholds, governance approvals, and constraint/lifecycle validation. |
| PD-011 | Proposed | Cryptographic/hash representation remains unresolved pending security/engineering review. |
| PD-012 | Proposed | Global-vs-tenant/platform-scope physical handling remains unresolved pending security/architecture review and isolation validation. |

## 5. Implementation boundary and governance conclusions

- **I-00–I-14:** boundaries and dependencies preserved/reconciled without silently widening scope. **I-06, I-07, I-09, I-12, I-13, and I-14 remain unauthorized.** No implementation increment is authorized by this correction.
- **Conditional readiness / planning recommendations:** do not convert to permission to implement.
- **ADR 0006:** remains **Proposed**; in-principle acceptance accurately recorded with bounded conditions/dependencies and provenance limitation.

## 6. Provenance limitation (preserved)

- `POSTGRESQL_SCHEMA_OPEN_DECISIONS.md` (blob `dc9a813be82bfa6ba1384b404d3805b67f2be88c`, 61 lines) and ADR 0006 markdown (blob `324a6eedcf7da9ced1294cc48a832e2c56bad99f`, 274 lines, Proposed) were recovered from agent checkpoint history (`278daf4623404f573132cee57e1d6fbe33b0846d`, 2026-11-21T16:11:58Z lineage context; checkpoint refs) and are **not** claimed present in the published Round 3 baseline or as part of public branch lineage with complete provenance. This limitation must be preserved in dependent reporting.

## 7. Traceability

- [POSTGRESQL_ROUND3_2_IMPLEMENTATION_AUTHORIZATION_MATRIX.md](./POSTGRESQL_ROUND3_2_IMPLEMENTATION_AUTHORIZATION_MATRIX.md)
- [POSTGRESQL_ROUND3_2_DEPENDENCY_AND_BLOCKER_MAP.md](./POSTGRESQL_ROUND3_2_DEPENDENCY_AND_BLOCKER_MAP.md)
- [POSTGRESQL_ROUND3_2_CHANGELOG.md](./POSTGRESQL_ROUND3_2_CHANGELOG.md)
- [POSTGRESQL_ROUND3_2_FINAL_REVIEW.md](./POSTGRESQL_ROUND3_2_FINAL_REVIEW.md)
- [adr/0006-atomic-per-tenant-asset-licensing.md](./adr/0006-atomic-per-tenant-asset-licensing.md)
- Round 3.1: [POSTGRESQL_ROUND3_1_OWNER_DECISION_REGISTER.md](./POSTGRESQL_ROUND3_1_OWNER_DECISION_REGISTER.md), [POSTGRESQL_ROUND3_1_OWNER_DECISION_BRIEFS.md](./POSTGRESQL_ROUND3_1_OWNER_DECISION_BRIEFS.md), [POSTGRESQL_ROUND3_1_BLOCKER_AND_DEPENDENCY_MAP.md](./POSTGRESQL_ROUND3_1_BLOCKER_AND_DEPENDENCY_MAP.md), [POSTGRESQL_ROUND3_1_FINAL_REVIEW.md](./POSTGRESQL_ROUND3_1_FINAL_REVIEW.md)
- Round 3/2/1.1 and physical/logical baselines as referenced in this branch.
