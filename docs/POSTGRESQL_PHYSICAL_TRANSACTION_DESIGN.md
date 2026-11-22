# CARES PostgreSQL Physical Transaction Design (Round 2)

**Status:** Proposed design documentation only; **NOT IMPLEMENTED, NOT TESTED**. This document maps Round 1 logical transaction boundaries to physical PostgreSQL behavior (tables, constraints, indexes, locking/concurrency intent, retries, and recovery). It does not define executable SQL/procedures/triggers or claim correctness under unvalidated workloads.

**Sources:** [POSTGRESQL_TRANSACTION_BOUNDARIES.md](./POSTGRESQL_TRANSACTION_BOUNDARIES.md), [POSTGRESQL_PHYSICAL_SCHEMA_DESIGN.md](./POSTGRESQL_PHYSICAL_SCHEMA_DESIGN.md), [POSTGRESQL_INDEX_STRATEGY.md](./POSTGRESQL_INDEX_STRATEGY.md), [POSTGRESQL_RLS_AND_TENANT_ISOLATION_DESIGN.md](./POSTGRESQL_RLS_AND_TENANT_ISOLATION_DESIGN.md), [POSTGRESQL_SCHEMA_OPEN_DECISIONS.md](./POSTGRESQL_SCHEMA_OPEN_DECISIONS.md).

## 1. Global physical transaction rules

- **Tenant context:** every tenant-scoped transaction requires verified, transaction-bound tenant context; fail closed if missing/invalid (no client-supplied tenant authority, no user-settable GUC authorization).
- **Isolation/concurrency (proposed baseline):** use PostgreSQL `READ COMMITTED` as default with explicit row locking (`SELECT ... FOR UPDATE`/`FOR NO KEY UPDATE` as appropriate) on contention points (usage state rows, ledger rows, outbox claims, binding/identity targets). `SERIALIZABLE` or additional conflict handling may be required for specific high-contention/correctness-critical cases after validation (assumption). Deadlocks handled by bounded retry with jitter and idempotent re-entry.
- **Atomicity:** each operation below defines the minimum set of state changes that must commit together in one DB transaction unless explicitly staged by approved design (OD-008 staged coupling is **not** approved).
- **Idempotency/no exactly-once external delivery:** identity/licensing operations use `core.identity_operation_idempotency_ledger` unique scope and deterministic canonical hash/state machine (OD-008 Proposed). Event acceptance uses `ingest.event_receipt` namespace uniqueness (OD-013). Outbox/external side effects are at-least-once with duplicate-safe handling and explicit unknown-outcome recovery; **no exactly-once external delivery is claimed**.
- **Constraints/indexes as correctness guards:** uniqueness/FK/CHECK constraints and supporting indexes are relied upon to detect conflicts atomically; application logic must handle constraint violations as deterministic outcomes (replay, duplicate, conflict, retryable failure).

## 2. Operation mapping

### Operation 1 — New canonical asset registration

- **Logical intent:** register a new canonical monitored asset for a tenant and bind it to an authoritative source-device identity without duplicate licensed usage.
- **Primary tables:** `core.identity_operation_idempotency_ledger`, `core.asset`, `core.asset_data_source`, optional `core.source_device_key`, `core.source_device_fingerprint_alias`, `core.asset_identity_claim`, `core.asset_lifecycle_event`, `core.tenant_license_usage_state`, `core.subscription_entitlement` (read/validate), `core.asset_license_event`, optional `core.asset_license_reservation`, `audit_evidence.audit_event`.
- **Key constraints/indexes:** `uq_identity_idempotency_scope`; `uq_asset_tenant_asset`; `uq_asset_data_source_source_device_key` (tenant, source_device_key_id); tenant-consistent FKs; usage-state checks/non-negative invariants (as approved).
- **Transaction boundary:** single DB transaction (proposed default, OD-008): insert/lock ledger row `in_progress` for scope key with canonical hash check → resolve/validate entitlement and lock `tenant_license_usage_state` row for update → verify no conflicting existing authoritative binding for same stable identity context → create asset + authoritative binding (+ optional dependent key row) + initial alias/claim/lifecycle/license records as required → update committed/reserved counters per approved semantics → mark ledger `committed` with outcome reference → write audit records.
- **Concurrency/locking:** row lock on ledger scope (via unique insert/conflict handling) and on `tenant_license_usage_state` for the tenant/scope; uniqueness constraints serialize competing bindings/registrations.
- **Failure/retry/recovery:** on duplicate key with same hash/state committed, return replayed outcome; same key different hash => terminal conflict (no state mutation); retryable DB failures before commit roll back; `timeout_unknown_commit` requires reconciliation before final outcome. Reservation expiry/compensation follows OD-003 if adopted.

### Operation 2 — Existing asset attachment from another data source

- **Logical intent:** attach an additional data source/binding evidence to an existing canonical asset (same unique monitored device) without creating duplicate licensed usage.
- **Primary tables:** `core.identity_operation_idempotency_ledger`, `core.asset` (lock/read), `core.asset_data_source`, `core.source_device_fingerprint_alias`, `core.asset_identity_claim`, `core.asset_lifecycle_event`, `audit_evidence.audit_event`.
- **Key constraints/indexes:** ledger uniqueness; binding uniqueness preventing conflicting authoritative mappings; tenant-consistent FKs.
- **Transaction boundary:** ledger insert/resolve → lock/validate target canonical asset and tenant → ensure resolved identity maps to same canonical asset and no competing binding → insert new `asset_data_source`/alias/claim/lifecycle records as applicable (no increment of committed licensed asset count for same device) → commit ledger/audit.
- **Concurrency/locking:** lock target asset/binding rows as needed; uniqueness guards prevent duplicate/conflicting attachments.
- **Failure/retry/recovery:** same as Operation 1; idempotent replay returns existing attachment outcome when committed.

### Operation 3 — Source-device fingerprint alias creation

- **Logical intent:** add a versioned fingerprint alias resolving to an existing stable authoritative binding identity.
- **Primary tables:** `core.source_device_fingerprint_alias`, `core.asset_data_source` (authoritative binding), `core.asset_identity_claim`/`core.asset_lifecycle_event` (as applicable), `audit_evidence.audit_event`, optionally ledger if modeled as idempotent identity operation.
- **Key constraints/indexes:** lookup/uniqueness index on fingerprint identity scope (partial/active semantics Proposed, OD-006); FK to binding; tenant consistency.
- **Transaction boundary:** verify trusted context and binding ownership → validate no ambiguous active alias conflict under approved rules → insert alias version with effective window/status → append provenance/lifecycle/audit records.
- **Concurrency/locking:** serialize conflicting alias inserts via uniqueness/locking on relevant scope; rotation overlap handled per approved policy.
- **Failure/retry/recovery:** constraint violation indicates duplicate/conflict; retry safe if operation key/idempotency used.

### Operation 4 — Fingerprint key/algorithm rotation

- **Logical intent:** rotate fingerprint material/algorithm while preserving the same immutable `source_device_key_id` and authoritative binding.
- **Primary tables:** `core.source_device_fingerprint_alias`, `core.asset_data_source`, `core.asset_lifecycle_event`, `audit_evidence.audit_event`, related claims/cases.
- **Key constraints/indexes:** alias version/effective uniqueness and history indexes; binding immutability for `source_device_key_id`.
- **Transaction boundary:** lock authoritative binding row → create/supersede alias versions with controlled overlap/effective timestamps → record lifecycle/audit events in same transaction. **No change** to `asset_data_source.source_device_key_id`.
- **Concurrency/locking:** binding-row lock to prevent concurrent conflicting rotation state.
- **Failure/retry/recovery:** rollback on validation/conflict; bounded overlap policy must be explicit (OD-006/007).

### Operation 5 — Identity conflict and pending resolution

- **Logical intent:** persist conflicting/ambiguous identity observations without creating incorrect canonical bindings or duplicate licensed usage.
- **Primary tables:** `core.identity_resolution_case`, `core.asset_identity_claim`, `core.asset_data_source`/`core.asset` (read), `core.asset_lifecycle_event`, `audit_evidence.audit_event`, optionally ledger in `failed_terminal`/pending outcome form as designed.
- **Key constraints/indexes:** FKs, case/claim status checks, tenant consistency.
- **Transaction boundary:** create/update resolution case and claim records, mark conflict state, emit audit/lifecycle records; **must not** allocate license or mutate canonical binding except through authorized resolution operation.
- **Concurrency/locking:** case-level locking if concurrent updates expected.
- **Failure/retry/recovery:** safe to append claims/case updates idempotently if dedup references used; manual/controlled resolution follows separate authorized transaction.

### Operation 6 — Asset merge

- **Logical intent:** merge duplicate canonical assets under authorization, preserving lineage/history and correctly adjusting licensing usage without ID reuse.
- **Primary tables:** `core.asset_merge_operation`, `core.asset`, `core.asset_lineage_link`, `core.asset_tombstone`, `core.asset_lifecycle_event`, `core.asset_data_source`/aliases/claims as reassigned, `core.tenant_license_usage_state`, `core.asset_license_event`, `core.identity_operation_idempotency_ledger` (if operation idempotent), `audit_evidence.audit_event`, evidence/authorization references as required.
- **Key constraints/indexes:** typed lineage mutual exclusivity check; unique tombstone per asset; ledger uniqueness if used; FKs; tenant consistency.
- **Transaction boundary (proposed):** authorize and lock participating assets/usage state rows → record merge operation → create typed `asset_lineage_link` rows (`link_type='merge'`, `merge_operation_id`) → reassign or rebind dependent records per approved rules → transition losing asset to terminal/tombstoned state (non-reusable) → apply licensing counter adjustments atomically per OD-003/004/005 → append lifecycle/license/audit records → commit ledger/outcome if used.
- **Concurrency/locking:** pessimistic locks on affected assets and tenant usage state; prevent concurrent conflicting merges/splits on same assets.
- **Failure/retry/recovery:** full rollback on failure; idempotent replay required if externally retried (operation key). Complex reassignment invariants need validation.

### Operation 7 — Asset split

- **Logical intent:** split one canonical asset into resulting assets under authorization with typed lineage and licensing/capacity enforcement.
- **Primary tables:** `core.asset_split_operation`, `core.asset` (source and resulting), `core.asset_lineage_link`, `core.asset_tombstone` (if source becomes terminal), `core.asset_lifecycle_event`, binding/alias/claim reassignment tables, `core.tenant_license_usage_state`, `core.asset_license_event`, ledger, `audit_evidence.audit_event`.
- **Key constraints/indexes:** typed lineage checks (`link_type='split'`, `split_operation_id`); uniqueness/FKs; capacity/entitlement checks.
- **Transaction boundary (proposed):** authorize and lock source asset + usage/entitlement context → validate resulting asset count/capacity and evidence requirements → create split operation and resulting assets/bindings/links → transition source asset per approved model (terminal/replaced or retained per policy, explicitly decided) → apply licensing deltas atomically → append records and commit.
- **Concurrency/locking:** locks on source and affected usage state; prevent double-split/conflicting operations.
- **Failure/retry/recovery:** rollback on insufficient capacity or invariant violation; idempotent operation handling required.

### Operation 8 — Asset deactivation/reactivation/removal

- **Logical intent:** change asset operational/licensing lifecycle state with correct historical records and non-reuse guarantees.
- **Primary tables:** `core.asset`, `core.asset_lifecycle_event`, `core.asset_license_event`, `core.tenant_license_usage_state`, `core.asset_tombstone` (for terminal removal states), `core.asset_data_source` status (as applicable), ledger, `audit_evidence.audit_event`.
- **Key constraints/indexes:** status checks, tombstone uniqueness, tenant-consistent FKs.
- **Transaction boundary:** lock asset and usage state as needed → validate permitted transition → update asset/lifecycle/licensing state and counters per approved semantics → create tombstone for terminal removal/representation if applicable → append events/audit and ledger outcome.
- **Concurrency/locking:** row locks prevent conflicting transitions.
- **Failure/retry/recovery:** deterministic rejection for invalid transitions; idempotent replay for same operation key.

### Operation 9 — Asset quota allocation/reservation/release

- **Logical intent:** atomically allocate, reserve, consume, or release licensed capacity for tenant/device operations.
- **Primary tables:** `core.tenant_license_usage_state`, `core.subscription_entitlement`, `core.asset_license_reservation` (if used), `core.asset_license_event`, `core.identity_operation_idempotency_ledger`, `core.asset`/operation references, `audit_evidence.audit_event`.
- **Key constraints/indexes:** `uq_tenant_license_usage_scope`; reservation status/time indexes; ledger uniqueness; CHECKs for non-negative counters (final formulas OD-003/004).
- **Transaction boundary:** ledger resolve → lock usage state (and reservation row if applicable) → validate entitlement/capacity under approved accounting model → apply committed/reserved deltas and reservation state transition → write license event/audit → commit.
- **Concurrency/locking:** mandatory `SELECT ... FOR UPDATE` on tenant usage state scope to serialize capacity checks/updates.
- **Failure/retry/recovery:** insufficient capacity is terminal business outcome (no partial commit); timeout/unknown commit reconciled via ledger and reservation state.

### Operation 10 — Event ingestion acceptance

- **Logical intent:** durably accept or deduplicate/reject an ingested event using explicit namespace rules and produce normalized/queryable records when accepted.
- **Primary tables:** `ingest.event_receipt`, `ingest.security_event`, `ingest.event_schema_reference`, `integration_ai.data_source`, `core.asset_data_source`/`core.asset` (attribution when resolved), optional `processing.processing_work_item`/`processing.outbox_message`, `audit_evidence.audit_event`.
- **Key constraints/indexes:** namespace-aware unique indexes on `ingest.event_receipt` (device-scoped upstream ID, data-source-global/fallback as applicable, OD-013); receipt-status and dedup-basis checks; FKs.
- **Transaction boundary:** validate schema/source/tenant context → determine dedup namespace and identity basis (upstream ID or explicit fallback fingerprint) → insert receipt; on uniqueness conflict detect duplicate and return/link duplicate outcome → for accepted non-duplicate events insert normalized `security_event` and any atomic downstream intent records (e.g. outbox/work item) in same DB transaction as acceptance where required → audit/correlate.
- **Concurrency/locking:** uniqueness constraints provide atomic dedup; avoid long transactions during high ingest rates.
- **Failure/retry/recovery:** retries safe due to dedup uniqueness; missing/unreliable upstream IDs follow explicit fallback policy (OD-013). **No identity ledger reuse** for event dedup.

### Operation 11 — Outbox claim and processing

- **Logical intent:** claim eligible outbox work safely across workers and record processing attempts without duplicate unsafe side-effect assumptions.
- **Primary tables:** `processing.outbox_message`, `processing.outbox_attempt`, optional `processing.processing_work_item`, `audit_evidence.audit_event`.
- **Key constraints/indexes:** claimable index on message status/availability; unique `(outbox_message_id, attempt_number)`; lease/heartbeat fields (OD-009 Proposed).
- **Transaction boundary (claim):** select eligible message with locking/skip-locked pattern (proposed) → verify lease/availability/state → create `outbox_attempt` (claimed/in_progress, lease token/expiry, attempt number) → update message status/last_attempt metadata → commit. **Processing/external execution occurs outside DB transaction**.
- **Concurrency/locking:** `FOR UPDATE SKIP LOCKED`-style claiming is a common physical pattern (design intent) to reduce contention; exact mechanism must be validated.
- **Failure/retry/recovery:** worker crash/lease expiry enables reclaim per policy; attempts recorded append-only; idempotent handlers required.

### Operation 12 — Outbox external delivery with unknown outcome

- **Logical intent:** record delivery outcomes including ambiguous/unknown external side effects and drive safe reconciliation/retry decisions.
- **Primary tables:** `processing.outbox_attempt`, `processing.outbox_message`, `audit_evidence.audit_event`, related domain tables only when a confirmed safe compensating/confirming state transition is justified.
- **Key constraints/indexes:** attempt status/lease indexes; message state checks.
- **Transaction boundary:** persist attempt outcome (`succeeded`, `failed_retryable`, `failed_terminal`, `unknown`) and corresponding message transition/next availability in a DB transaction after external interaction result (or timeout/ambiguity) is observed. Unknown outcomes must remain visible for reconciliation.
- **Concurrency/locking:** lock attempt/message rows during state transition.
- **Failure/retry/recovery:** retries permitted only when handler and external contract are idempotent or safely deduplicated; **unknown delivery is not treated as success**; no exactly-once external delivery claimed (OD-009).

### Operation 13 — Forensic evidence creation and controlled transition

- **Logical intent:** create evidence metadata/versions and perform controlled, authorized state transitions while preserving integrity, custody, and tenant isolation.
- **Primary tables:** `audit_evidence.forensic_evidence_record`, `audit_evidence.evidence_object_version`, `audit_evidence.evidence_custody_event`, `audit_evidence.evidence_transition_authorization`, `audit_evidence.audit_event`, related asset/case references.
- **Key constraints/indexes:** unique `(forensic_evidence_record_id, version_number)`; FKs; status/transition checks; legal-hold enforcement in application/procedure logic plus recorded flags.
- **Transaction boundary (creation):** insert evidence record and initial immutable version/custody metadata atomically with audit correlation; external object storage upload/verification sequencing must be handled to avoid untracked artifacts (procedure design required). **Controlled transition:** verify authorization, legal hold, and allowed transition → record authorization decision/transition event → update evidence status only as permitted → append custody/audit records in same transaction.
- **Concurrency/locking:** lock evidence record for transition checks; append-only custody/version rows.
- **Failure/retry/recovery:** no silent deletion/overwrite; failed transitions leave prior state intact; external storage/object existence and hash verification may require compensating reconciliation procedures (risk documented).

## 3. Cross-operation consistency notes

- **Idempotency scope separation:** `core.identity_operation_idempotency_ledger` is for identity/licensing operations only; `ingest.event_receipt` is for event ingestion dedup only; outbox attempt/message state provides delivery coordination/retry history (not external exactly-once guarantee).
- **Typed lineage only:** merge/split effects must be represented via typed `asset_lineage_link` references and operation records.
- **Licensing atomicity:** committed/reserved usage mutations, when applicable, occur in the same DB transaction as the corresponding validated operation outcome (default coupling) per OD-008; accounting semantics remain Proposed pending OD-001/003/004.
- **RLS/privileges:** all operations execute under least-privilege runtime roles with verified transaction-bound tenant context; maintenance/admin exceptions are controlled and audited.
