# ADR 0006: Enforce per-tenant asset quota atomically in PostgreSQL

- **Status:** Proposed (mandatory licensing semantics preserved; transactional/licensing design proposed pending owner approval and formal schema/security review)
- **Date:** 2026-11-16
- **Last reviewed/updated:** 2026-11-21 (documentation-only consistency review; no implementation)
- **Round 3.2 governance reconciliation:** 2026-11-22 (documentation-only consolidation; see “Round 3.2 owner decision consolidation and governance reconciliation” below)

## Problem

The one-device-one-asset rule is not reliable if concurrent enrollments both pass an in-memory quota check, if a retry creates another asset, if source attachment increments usage, or if fingerprint rotation/merge/split operations create duplicate bindings, assets, or licensed usage. Licensing must be per tenant, authoritative in PostgreSQL, and remain consistent through registration, attachment, conflict resolution, merge, split, deactivation, reactivation, removal, fingerprint rotation, and recovery.

## Confirmed requirements (preserved)

- **Mandatory commercial invariant:** every unique monitored device consumes exactly one licensed asset. Multiple data sources reporting the same device must **not** create duplicate licensed assets.
- Python backend.
- PostgreSQL is the authoritative licensing database/system of record for licensing and identity enforcement.
- SaaS-only external AI providers; no local GPU requirement. (AI is not an authority for licensing, identity, merge/split, or quota decisions.)
- Asset licensing is separate from technical resource quotas (ingestion, storage, agent count, API capacity, AI usage, etc.).
- Each tenant has licensed asset entitlement/quota, licensing state/history, and auditable lifecycle/removal evidence.
- Licensing enforcement and commercial reporting must agree across backend, API, and Dashboard when implemented.
- All controls described here are **proposed, NOT IMPLEMENTED, and NOT TESTED** unless actual repository evidence proves otherwise.

## Alternatives considered

1. **Process-local counter/check.** Simple but lost on restart and vulnerable to concurrent races and duplicate billing; rejected.
2. **Count database rows on every registration without locking/serialization.** A concurrent check-then-insert can exceed quota or race with merge/split; rejected.
3. **Per-tenant serialized licensing transaction in PostgreSQL with tenant-inclusive uniqueness constraints, stable binding/alias separation, idempotency ledger, and append-only history.** Correctness-oriented and compatible with PostgreSQL as reference implementation at the proposed initial scale; selected as the proposed direction.
4. **Distributed lock or external quota service.** Adds infrastructure and failure modes before there is evidence that PostgreSQL transaction/locking design is insufficient; deferred pending measured contention evidence.

## Proposed decision

### 1. Stable source-device binding and fingerprint aliases (conceptual alignment)

Align with the latest `docs/DATA_ARCHITECTURE.md` and architecture decision packages: a fingerprint is evidence/lookup material, **not** the permanent identity of a binding.

**Conceptual separation (proposed):**

- **`asset_data_source`**: stable relationship between a canonical CARES asset and a data-source/device identity context (tenant-scoped). It represents that a specific source/device binding is attached to a canonical asset; it is not itself a billable asset count.
- **`source_device_key_id`**: stable internal identity for the source-device binding (CARES-generated, tenant/source-scoped as designed). It remains stable across fingerprint algorithm/key-version rotations and alias overlap for that same binding.
- **`source_device_fingerprint_alias`**: versioned fingerprint aliases associated with the stable binding (`source_device_key_id` / binding identity). Multiple aliases may be active/valid during an approved overlap window and must resolve to the same stable binding.

**Binding uniqueness (proposed):**
- One `source_device_key_id` identifies one stable source-device binding within its tenant/data-source context and maps to at most one canonical CARES asset at a time per approved lifecycle/invariant rules.
- `asset_data_source` / binding records must be tenant-inclusive and must prevent the same stable source-device binding from being attached to multiple canonical assets or duplicated as a conflicting active binding.
- A single `data_source_id`/connector instance may report many devices (many bindings/`source_device_key_id` values); one canonical asset may have bindings from many sources. Adding/attaching bindings to an already-resolved canonical asset does **not** create another licensed asset or increment licensed usage.

**Alias uniqueness (proposed):**
- Alias uniqueness must be tenant-scoped and include, at minimum, the dimensions required by the approved design: tenant, data source/binding context, algorithm, key version, and protected fingerprint value (or equivalent approved uniqueness tuple). Exact DDL/constraint names are illustrative and subject to formal schema review.
- No uniqueness constraint may use an unprotected raw source identifier as the key. Raw identifiers, if retained by approved policy, are protected sensitive data and not identity keys.
- A fingerprint/alias row must be tenant- and source/binding-consistent via tenant-inclusive foreign keys/constraints so aliases cannot be attached across tenants or to the wrong binding.

**Multiple active/overlap aliases mapping to one stable binding (proposed):**
- During approved overlap, multiple active aliases (for example old and new algorithm/key-version fingerprints) may reference the same stable `source_device_key_id`/binding.
- All such aliases must resolve to the same canonical asset/binding; overlap does not authorize creation of a second binding, second asset, or additional licensed usage.

**Atomic registration and fingerprint rotation (proposed):**
- Registration must atomically: verify tenant context/authorization, resolve identity/aliases, lock required licensing rows in defined order, recheck uniqueness/state after lock, create or attach binding/aliases/asset/lifecycle records as applicable, apply licensing counter/history effects, and persist idempotency outcome/result in one PostgreSQL transaction.
- Fingerprint rotation must atomically per approved batch/step: add new alias/version material, preserve required overlap state, verify lookup/uniqueness/binding consistency, update alias state/retirement markers as approved, and record audit/history. Rotation must not rewrite identity history in place.

**Lookup behavior during overlap (proposed):**
- Lookup accepts any currently valid/active alias for the approved overlap window and resolves to the same stable binding/canonical asset.
- If lookup finds no valid binding, treat as unresolved/new-candidate per identity rules (not automatic merge). If lookup finds conflicting bindings/assets, fail closed to conflict/pending review; do not create or merge assets automatically.

**Collision handling (proposed):**
- A uniqueness violation or conflicting alias-to-binding/asset resolution is a conflict, not permission to create a duplicate binding/asset. The transaction must roll back or transition to an explicit conflict/pending-resolution path per approved design; no duplicate licensed usage may be committed.
- Fingerprint collisions or ambiguous mappings require investigation/review controls as approved; weak/corroborating attributes never authorize automatic merge.

**Migration behavior (proposed):**
- Migration/re-fingerprinting/reprocessing must be idempotent, resumable, and auditable.
- It must **not** create duplicate assets, duplicate active bindings, duplicate aliases violating uniqueness, or duplicate/inflated licensed usage.
- Old and new aliases may overlap only for the approved period and must map to the same stable binding. Retirement/deactivation of old aliases/keys must preserve required audit history and follow approved retention/security policy.

### 2. Explicit licensing accounting model (proposed technical model)

This section defines a **proposed technical model** to support owner-approved commercial decisions. It does **not** invent commercial decisions.

**Separated measures:**

- **Active billable usage:** count of canonical monitored assets currently in billable/active licensed state per tenant, as defined by approved policy mapping. One unique monitored device = one licensed asset when active/billable.
- **Reserved capacity:** quota capacity held/reserved by approved lifecycle or policy states (for example grace/reservation mechanics) that is not necessarily the same as active billable usage.
- **Pending identity reservation:** provisional capacity reserved for an unresolved/pending identity case, if owner-approved; it does not by itself confirm a billable monitored device.
- **Available capacity:** remaining capacity that may be allocated/reserved for new billable assets or approved reservations according to approved policy.
- **Historical/tombstone records:** retained lifecycle/licensing/audit identity records for deactivated/merged/removed/resolved cases; they preserve history and do not imply active billable usage or available capacity unless an approved state mapping explicitly states otherwise.

**Proposed accounting equations (illustrative, subject to owner policy mapping):**

- `available_capacity = entitled_quota - active_billable_usage - reserved_capacity - pending_identity_reservation_adjustment`
  - where `pending_identity_reservation_adjustment` is included only to the extent pending cases reserve capacity under approved policy (possibly equal to pending reservation count/slots, possibly zero).
- `entitled_quota` is the effective tenant entitlement/quota at the time of the transaction (effective-dated/audited as designed).
- All counters are tenant-scoped, non-negative by invariant, and updated only by authorized atomic transactions with append-only licensing/lifecycle history.

**Proposed state-to-counter mapping (technical support model; commercial meaning owner-approved):**

| State / record | Active billable usage | Reserved capacity | Pending identity reservation | Available capacity effect | Historical/tombstone record |
|---|---:|---:|---:|---|---|
| Active canonical asset (billable) | +1 (if policy maps active as billable) | 0 unless separately reserved | 0 | Consumes available capacity | Current active record plus history |
| Deactivated with approved grace reservation | 0 or policy-defined (owner decision) | +1 or policy-defined (owner decision) | 0 | May consume/reserve capacity during grace | Retained lifecycle history |
| Pending identity reservation | 0 (not a confirmed billable monitored device) | 0 unless policy defines otherwise | +1 if owner approves reservation; else 0 | May consume capacity only if owner approves | Pending-resolution history |
| Merged losing asset (tombstone) | 0 | 0 | 0 | Released only per approved merge accounting; survivor remains billable as applicable | Retained tombstone/history (never reused ID) |
| Removed/tombstone after approved removal | 0 | 0 unless policy defines otherwise | 0 | Released only per approved removal/grace policy | Retained tombstone/history |
| Reactivated to active | becomes +1 per policy | releases applicable reservation | 0 | Recomputed atomically | Append-only lifecycle history |

**Owner decisions required (must be clearly labeled):**
- Whether reserved slots consume billable quota.
- Whether pending identity cases reserve capacity.
- Pending reservation duration.
- Deactivation grace period.
- Immediate quota release exceptions.
- Permanent removal authorization.

The database model must support these decisions through explicit state mapping, effective-dated entitlements/policy versions (as designed), and counter/history fields **without redesigning the core identity structure** (`canonical asset`, `asset_data_source`/stable binding, `source_device_key_id`, versioned fingerprint aliases).

### 3. Atomic merge and split (proposed, NOT IMPLEMENTED)

**Authorization and evidence requirements (proposed):**
- Tenant-scoped, privileged, authenticated/authorized operation with explicit reason, evidence references, and audit record.
- Required approvals (including any multi-person approval) are **owner/security decisions**.
- Manual/assisted actions must never be authorized by untrusted input or AI output.

**Stable canonical asset selection (proposed):**
- Merge explicitly selects a surviving canonical asset; losing canonical asset IDs become tombstones/merged records and are never reused.
- Split creates a new canonical asset UUID (never reused) while preserving the original asset/binding/event lineage as required.

**Source-binding reassignment (proposed):**
- Merge: eligible `asset_data_source` bindings (and associated stable `source_device_key_id` contexts as applicable) are reassigned to the survivor only when tenant/uniqueness/conflict checks pass; ineligible/conflicting bindings remain blocked for review.
- Split: specified bindings/claims move to the new or retained canonical asset according to approved rules; no binding may be duplicated or left ambiguously attached.
- Fingerprint aliases remain attached to their stable binding unless a separately approved, auditable rebinding operation is required; alias-to-binding consistency must be preserved.

**Atomic licensing and lineage preservation (proposed):**
- A merge or split transaction must atomically: validate tenant/policy/authorization context, lock affected licensing/asset/binding rows in defined order, recheck state/uniqueness/conflicts, update canonical/tombstone/binding relationships, append lineage/merge-split records, update active billable/reserved/pending counters according to approved mapping, append licensing history, write audit/evidence linkage, and persist idempotency outcome/result.
- The operation must preserve stable lineage/history and must not create duplicate assets, duplicate bindings, duplicate aliases, or duplicate/inflated licensed usage.

**Rollback and idempotency behavior (proposed):**
- If any precondition, uniqueness, policy, or accounting invariant fails, the transaction rolls back with no partial merge/split/licensing effects.
- Retries with the same tenant-scoped idempotency key and equivalent request must return/reconcile the recorded outcome (completed, failed, or pending/recovering per ledger state) without applying effects twice.
- Requests with the same idempotency key but different payload/target/effect must be rejected as conflicts.

**Unresolved-identity interaction (proposed):**
- Assets/bindings in pending/unresolved identity states must not be merged/split in a way that finalizes licensing incorrectly; resolution, reservation handling, and billing-impacting transitions require approved policy and explicit workflow state.

### 4. Idempotent operations (proposed, NOT IMPLEMENTED)

Idempotency applies to registration, attachment, rotation, merge, split, deactivation, reactivation, removal, conflict-resolution transitions, and recovery/retry flows that can affect identity, bindings, aliases, lifecycle state, counters, or history.

**Idempotency key concept (proposed):**
- The caller/worker supplies a tenant-scoped idempotency key per logical operation instance (or the system derives an approved deterministic key from a stable external event/request identifier). The key must be bound to tenant, operation type, and request fingerprint/hash as designed.

**Ledger/recording expectations (proposed):**
- A durable tenant-scoped idempotency ledger records operation identity, tenant, operation type, request hash/fingerprint, processing/completed/failed state, result reference/outcome, timestamps, and correlation identifiers.
- A successful or definitively failed idempotent operation produces at most one logical effect and one canonical recorded outcome for that key+request; retries read/replay the ledger outcome.
- Unknown commit (for example timeout after commit uncertainty) must be recoverable by consulting the ledger/state and must not create duplicate effects.

**Replay/duplicate handling (proposed):**
- Duplicate/replayed requests: no second asset, binding, alias, lineage record, counter increment/decrement, or history side effect.
- Conflicting requests reusing a key with different intent/payload: reject and audit.

### 5. PostgreSQL concurrency control (proposed, reference strategy)

**Target isolation level (proposed):** `READ COMMITTED` with explicit row locking and uniqueness-constraint enforcement for critical licensing/identity transactions. Serializable may be considered only if validated for contention/latency; not assumed.

**Lock ordering (proposed, must be defined and consistent):**
- Acquire locks in a deterministic order to reduce deadlocks, for example: tenant licensing/entitlement/usage row(s) -> canonical asset row(s) in stable ID order -> stable binding/`asset_data_source`/`source_device_key` row(s) in stable ID order -> alias/fingerprint rows as needed.
- Use `SELECT ... FOR UPDATE` (or equivalent approved lock strength) on rows that gate quota, canonical identity, binding reassignment, or state transitions.

**Uniqueness and recheck after lock (proposed):**
- Enforce tenant-inclusive uniqueness/foreign-key constraints as the final guard against races.
- After acquiring required locks, recheck quota/capacity, asset/binding/alias existence, lifecycle state, merge/split eligibility, and idempotency outcome before mutating state.

**Retry/deadlock handling (proposed):**
- Application/service logic may retry transient serialization/deadlock/lock-timeout failures with bounded backoff and the same idempotency key; retries must be safe and must not duplicate effects.
- Constraint violations representing true conflicts/duplicates must not be blindly retried as success-creating operations.

### 6. Transaction boundaries (proposed)

For each multi-step operation below, all database writes affecting identity, licensing counters, lifecycle state, lineage, and idempotency outcome must occur in **one PostgreSQL transaction** (or a formally proven equivalent with compensating controls; none proposed/approved):

- **Registration/identity resolution that allocates a new licensed asset:** tenant/entitlement validation, alias/binding lookup, lock/recheck, capacity/quota check, canonical asset creation (if needed), stable binding/alias creation, counter/history updates, idempotency result.
- **Attachment of additional source to existing canonical asset:** validate resolved canonical asset/binding, create/attach binding/alias records as approved, append history/audit linkage; **no licensed-usage increment**.
- **Fingerprint rotation/overlap update:** alias insert/state changes, binding consistency checks, audit/history, idempotency result.
- **Merge:** authorization/evidence linkage, lock/recheck, binding reassignment, tombstone/lineage creation, counter reconciliation per approved mapping, history/audit, idempotency result.
- **Split:** authorization/evidence linkage, lock/recheck, new canonical asset creation, binding reassignment, lineage creation, counter reconciliation per approved mapping, history/audit, idempotency result.
- **Deactivation/reactivation/removal:** state transition, grace/reservation/capacity effects per approved policy, tombstone/history where applicable, audit, idempotency result.

### 7. Audit and licensing history requirements (proposed)

**Append-only history expectations (proposed):**
- Licensing entitlement/quota changes, usage/counter-affecting transitions, merge/split lineage, deactivation/reactivation/removal, fingerprint rotation/alias lifecycle, conflict resolution outcomes, and idempotency outcomes must be recorded as append-only history/events where applicable (no in-place rewrite of historical facts except approved correction patterns with full audit trail, if ever defined).
- Canonical asset IDs, stable `source_device_key_id`/binding IDs, and historical licensed-asset/tombstone identities are never reused.

**Linkage requirements (proposed):**
- Every licensing/identity-affecting transaction links to tenant, actor/service identity, correlation/request ID, idempotency key (where applicable), affected canonical asset(s), affected bindings/aliases, reason/evidence references for manual/exception operations, and resulting counter/state snapshot or delta as designed.
- Audit records must be sufficient to explain why capacity was consumed, reserved, released, or preserved and to support reconciliation between backend, API, and Dashboard reporting when implemented.

**Operational telemetry distinction (proposed):** licensing/identity history and audit evidence are not the same as operational telemetry; telemetry must not be used as the authority for licensing decisions.

## Rationale

- **Correctness and commercial protection:** PostgreSQL transactions, tenant-scoped serialization/locking, tenant-inclusive uniqueness constraints, and idempotency are the authoritative controls to prevent duplicate licensed assets and quota races.
- **Stable identity model:** separating canonical assets, stable bindings, stable `source_device_key_id`, and versioned fingerprint aliases supports rotation, overlap, merge/split, and recovery without treating fingerprints as permanent identity.
- **Auditability and recovery:** append-only history, lineage, tombstones, and idempotency ledgers enable reconciliation and safe retries after partial failures/timeouts.
- **Operational simplicity (initial):** a single PostgreSQL authority avoids premature distributed coordination while preserving a path to evolve if measured contention requires it.

## Consequences

**Benefits:**
- Aligns proposed enforcement with the mandatory one-device-one-asset invariant and no-duplicate-asset rule across sources.
- Provides a clear conceptual model for quota accounting, merge/split, rotation, and idempotent retries.
- Improves reviewability for future schema/security/implementation work and highlights required owner decisions.

**Costs/risks:**
- Per-tenant serialization/locking can increase contention for tenants with high concurrent registration or lifecycle operations.
- Additional schema complexity (bindings, aliases, ledgers, history, tombstones, state mappings) and stricter operational procedures for merges/splits/rotations.
- Incorrect lock ordering or incomplete recheck logic can cause deadlocks or correctness gaps if later implemented poorly.
- Owner-approved policy choices (reservations, grace periods, pending behavior) materially affect counter semantics and must be resolved before implementation.

**Operational impact (when/if implemented):**
- Requires monitored contention metrics, deadlock/constraint-violation telemetry, reconciliation jobs, and runbooks for conflict resolution, rotation, merge/split, and recovery.
- Requires production-equivalent validation of RLS/verified tenant context behavior and concurrent transaction scenarios.

## Verification requirements

These are **required proposed verification scenarios** for future implementation and testing. They are **NOT** executed in this documentation update.

**Required PostgreSQL concurrency tests (proposed):**
- Concurrent registration of the same device/fingerprint alias and different aliases resolving to the same binding must not create duplicate assets, bindings, or licensed usage.
- Concurrent registration attempts at quota boundary must not exceed entitled/allowed capacity under the approved policy mapping.
- Concurrent merge/split/attach/rotate/deactivate/reactivate/remove operations on overlapping entities must preserve invariants, lineage, and counter correctness or fail safely.
- Deadlock/retry paths must be exercised with idempotency keys to confirm no duplicate effects.

**RLS validation expectations (proposed):**
- All licensing, binding, alias, asset, counter, history, and idempotency access paths must be validated under tenant-scoped RLS/verified transaction context using production-equivalent, non-owner roles.
- Cross-tenant reads/writes, tenant-context spoofing, and missing-context behavior must be tested and must fail closed.

**Idempotency verification (proposed):**
- Replayed identical requests (including after timeout/unknown commit) return consistent outcomes with no duplicate logical effects.
- Conflicting payloads with the same idempotency key are rejected and audited.
- Ledger/result retention and recovery behavior are verified for supported retry windows.

**Fingerprint rotation verification (proposed):**
- Overlap-period lookups resolve old/new aliases to the same stable binding/canonical asset.
- Rotation does not create duplicate bindings/assets/aliases or inflate licensed usage.
- Retirement of old aliases/keys preserves required history and respects approved retention/security controls.

**Merge/split verification (proposed):**
- Authorized merge preserves survivor, tombstones losing IDs, reassigns eligible bindings, reconciles counters correctly, and maintains lineage/audit.
- Authorized split creates a new non-reused canonical asset, reassigns specified bindings correctly, reconciles counters correctly, and maintains lineage/audit.
- Unauthorized, conflicting, or invalid merge/split attempts fail atomically with no partial effects.

**Audit and reconciliation verification (proposed):**
- Append-only licensing/history records are complete and linked for all counter-affecting and identity-affecting operations.
- Reconciliation can explain active/reserved/pending/available/historical states per tenant under the approved policy mapping.
- Backend/API/Dashboard licensing views (when implemented) agree with PostgreSQL-authoritative records.

## References

- [docs/DATA_ARCHITECTURE.md](../DATA_ARCHITECTURE.md)
- [docs/POSTGRESQL_TECHNICAL_DECISIONS.md](../POSTGRESQL_TECHNICAL_DECISIONS.md)
- [docs/ARCHITECTURE.md](../ARCHITECTURE.md)
- [docs/SECURITY_ARCHITECTURE.md](../SECURITY_ARCHITECTURE.md)

## 2026-11-21 documentation-only consistency review

### What was reconciled
- Aligned this ADR to the current stable source-device identity model: **`asset_data_source` + stable `source_device_key_id` + versioned `source_device_fingerprint_alias`** with fingerprint-as-lookup-evidence (not permanent identity), tenant-inclusive uniqueness concepts, overlap alias resolution to the same stable binding, and no duplicate licensed asset/binding/alias/usage on registration, attachment, rotation, migration, merge, or split.
- Made mandatory licensing invariants explicit and preserved: one unique monitored device = one licensed asset, multiple sources for the same device do not create duplicate licensed assets, PostgreSQL is the authoritative licensing database, and adding bindings to an existing canonical asset does not increment licensed usage.
- Expanded the proposed licensing accounting model to separate **active billable usage, reserved capacity, pending identity reservation, available capacity, and historical/tombstone records**, with illustrative equations/state mapping and explicit owner-decision labels.
- Added proposed atomic **merge/split** requirements (authorization/evidence, stable canonical selection, tombstones/no ID reuse, binding reassignment, lineage preservation, counter reconciliation, rollback/idempotency).
- Added proposed **idempotency** requirements (tenant-scoped keys, durable ledger/outcome recording, replay/conflict handling, unknown-commit recovery) and clarified concurrency/transaction expectations.
- Defined a proposed durable, tenant-scoped idempotency ledger model with operation type/request hash, processing/completed/failed semantics, stored results/references, duplicate/conflict handling, and retry behavior after unknown commit/lifecycle transitions.
- Expanded verification requirements to required proposed PostgreSQL concurrency/RLS/idempotency/rotation/merge-split/reconciliation scenarios using production-equivalent non-owner runtime roles; explicitly distinguished proposed tests from executed tests.

### Remaining technical uncertainties
- Final PostgreSQL schema/DDL, constraint names, index strategy, partitioning interactions, and exact uniqueness tuples for bindings/aliases/idempotency records require formal schema review.
- Exact transaction boundaries, lock granularity, deadlock/retry policy, and contention behavior under representative workloads are unmeasured.
- Final mapping of lifecycle states to counters under owner-approved commercial policy (especially reserved/pending/deactivation/removal semantics) requires policy-to-schema validation.
- Interaction details with verified transaction context/RLS helper design, background workers, outbox/reconciliation jobs, and controlled evidence/approval workflows require end-to-end design and security review.
- Fingerprint algorithm/key management, rotation batch sizing, overlap duration mechanics, collision investigation workflow, and retention/deletion of old aliases/raw identifiers remain design/operational uncertainties.

### Owner decisions still required
- Whether reserved slots consume billable quota.
- Whether pending identity cases reserve capacity.
- Pending reservation duration.
- Deactivation grace period.
- Immediate quota release exceptions.
- Permanent removal authorization.
- Commercial billing semantics for active assets versus reserved slots and any grace/reservation period.
- Merge/split/removal approval model (including any multi-person approval), evidence sufficiency, and authorized roles.
- Idempotency ledger retention/pruning period and audit/reconciliation requirements.

### Consistency with DATA_ARCHITECTURE.md and the latest architecture decision package
- **Consistent/preserved:** one unique monitored device = one licensed asset; multiple sources reporting the same device must not create duplicate licensed assets; PostgreSQL as authoritative licensing database; Python backend; SaaS-only external AI/no local GPU; licensing separated from technical resource quotas; tenant-scoped atomic/idempotent enforcement; append-only history/tombstones; no automatic merge on weak/conflicting identity.
- **Aligned in this ADR:** stable binding/alias separation (`asset_data_source`, `source_device_key_id`, `source_device_fingerprint_alias`), fingerprint as non-permanent identity, tenant-inclusive uniqueness/recheck concepts, merge/split/rotation need for atomicity and no duplicate usage, and PostgreSQL reference concurrency/idempotency expectations.
- **Remaining alignment work (documentation/schema review):** exact terminology/field names and constraint details must continue to be reconciled across `DATA_ARCHITECTURE.md`, architecture decision packages/final corrections, and future formal schema/security review (especially final alias/binding table definitions, verified-context/RLS integration details, approved state-to-counter mappings, and operation-by-operation transaction boundaries). Proposed technical options and dependencies are prepared in [POSTGRESQL_TECHNICAL_DECISIONS.md](../POSTGRESQL_TECHNICAL_DECISIONS.md). This ADR remains a proposed consistency/reference update, not a schema or implementation specification. Status remains **Proposed** (not accepted).

### Confirmation
- No application source code, PostgreSQL schema files, migrations, or test files were modified.
- ADR remains **proposed** until approved through the required architecture/owner/security review process.
- No PostgreSQL tests have been run or claimed as passed; all verification requirements above are proposed.

## Round 3.2 owner decision consolidation and governance reconciliation

**Record type:** documentation-only governance reconciliation (2026-11-22). **No database implementation or runtime code was created or authorized by this reconciliation.** No DDL, migrations, ORM models, database roles/policies, triggers/stored procedures, provisioning scripts, application code, runtime configuration, or production infrastructure were created or modified.

### Authoritative input (current project conversation)
- The owner has **approved the principles and bounded conditions of all thirteen Owner Decisions (OD-001 through OD-013)** for governance consolidation purposes.
- **OD-001:** the owner has approved **acceptance of ADR 0006 in principle** with the agreed bounded exclusions and preserved deferred dependencies. This **does not** constitute unconditional formal ADR status transition.
- Approval of bounded principles/conditions **must not** be interpreted as approval of unresolved technical details, final formulas/predicates/mechanisms/policies not explicitly specified, or authorization for any implementation increment.

### Approved principles preserved (ADR 0006 / licensing-accounting governance context)
The following principles are explicitly preserved as owner-approved in principle (bounded):
1. **One unique monitored device per tenant equals one licensed asset.**
2. **Multiple sources reporting the same device must not cause duplicate licensing.**
3. **Device types have equal licensing weight.**
4. **Asset licensing remains separate from technical resource quotas.**
5. **PostgreSQL is the transactional authority for licensing accounting and quota enforcement.**
6. **Concurrent operations must not cause oversubscription or duplicate business effects.**

### Bounded exclusions and deferred dependencies (explicitly retained)
The following remain **not resolved, not finalized, and not authorized** by this in-principle acceptance and must not be silently closed:
- Reservation policy details (including whether/when/how pending identity reservations reserve capacity, duration/timeout/release/representation, and policy-to-schema mapping).
- Counter transitions, authoritative counter scope, and recomputation/reconciliation semantics/formulas.
- Merge/split accounting edge cases and all merge/split authorization/evidence/licensing-effect details pending required approvals.
- Unresolved lifecycle details (including but not limited to deactivation grace/removal/re-enrollment/reset interactions as governed by OD/PD decisions).
- Formal idempotency contract approval details, coupling-mode approval, canonicalization/hash/state/retention/reconciliation specifics, and staged-exception approvals (OD-008).
- ADR 0006 schema-level interpretation finalization where still ambiguous; any required formal schema/security/architecture review and acceptance process.
- All other OD-001–OD-013 and PD-001–PD-012 unresolved technical details, validations, and governance approvals as recorded in the Round 3.2 Owner Decision Register and dependency/blocker reconciliation.

### Formal ADR status transition — explicitly pending (not mechanically changed)
- **Recorded formal ADR status remains:** **Proposed** (as stated above). This reconciliation **does not** mechanically change ADR 0006 to “Accepted”.
- **Reason:** unconditional/formal ADR status transition requires verification and completion of the applicable ADR governance/acceptance requirements (including formal review/acceptance record as required by project governance) and must accurately reflect bounded acceptance versus excluded/deferred technical details. Those formal governance steps and records are **not** completed by this documentation-only consolidation.
- **Distinction preserved:** OD-001 records **acceptance of ADR 0006 in principle with agreed bounded exclusions**; this is distinct from, and does not replace, an unconditional formal ADR status transition. Any future formal status change must be explicitly documented, evidence-backed, and consistent with resolved exclusions/dependencies.

### Implementation and authorization impact
- **No implementation authorized.** OD approvals and this in-principle ADR acceptance do not authorize I-06, I-07, I-09, I-12, I-13, I-14, or any other implementation increment.
- Any future implementation requires separate, explicit owner authorization records per increment/scope, satisfied prerequisites/approvals/validations, and compliant technical design—none of which are granted by this task.

## Revisit when

Measured per-tenant registration contention violates declared objectives, owner-approved lifecycle/commercial policy requires different state mapping, or formal schema/security review identifies required structural changes. Any revision must preserve the one-device-one-asset invariant, no-duplicate-licensed-asset rule, historical licensing evidence, and tenant isolation.

## Round 3.2.1 owner decision fidelity correction (documentation-only)

**Record type:** documentation-only governance fidelity correction (2026-11-22, UTC). **No database implementation or runtime code was created or authorized.** No DDL, migrations, ORM models, database roles/policies, triggers/stored procedures, provisioning scripts, application code, runtime configuration, or production infrastructure were created or modified.

### OD-001 authoritative clarification (preserved without reinterpretation)
- The owner approved **ADR 0006 in principle**, subject to the previously specified bounded conditions. **ADR 0006 concerns atomic per-tenant asset licensing/accounting of monitored devices; it is not the CARES software subscription license.**
- **Bounded conditions/prohibitions preserved:** one unique monitored device represents exactly one licensed asset per tenant; multiple reporting sources for the same device must not double-count it; all device types have equal licensing weight (no OS-/vendor-/device-type-/telemetry-volume-based weighting); asset licensing remains separate from technical resource quotas; dependencies on **OD-003, OD-004, and OD-008** are preserved.
- **Status/governance:** do **not** represent the owner’s approval in principle as unconditional formal ADR acceptance. **Formal ADR status remains Proposed** unless a separate formal ADR governance action explicitly changes it (none provided). Approval in principle does **not** authorize implementation.
- **Deferred details remain deferred:** reservation lifecycle/expiration/recovery/concurrency/accounting mechanics (OD-003), counter-maintenance/reconciliation scheduling/repair/locking/strategy/edge cases and numerical/operational policies (OD-004), merge/split edge cases/transition rules/accounting implementation (OD-005), formal idempotency contract/coupling/canonicalization/retention/reconciliation/unknown-commit details (OD-008), schema-level interpretation/finalization and required formal reviews/validations.

### Provenance limitation (preserved)
Recovered ADR 0006 source material (blob `324a6eedcf7da9ced1294cc48a832e2c56bad99f`, 274 lines, **Status: Proposed**) was recovered from agent checkpoint history/commit `278daf4623404f573132cee57e1d6fbe33b0846d` (2026-11-21T16:11:58Z lineage context), not the published Round 3 branch lineage; full provenance is not claimed as part of public branch lineage. Cross-reference: [POSTGRESQL_ROUND3_2_OWNER_DECISION_REGISTER.md](../POSTGRESQL_ROUND3_2_OWNER_DECISION_REGISTER.md) (Round 3.2.1 fidelity-corrected).
