# CARES PostgreSQL Physical Schema Design (Round 2)

**Status:** Proposed physical schema design documentation only; **NOT IMPLEMENTED, NOT TESTED**. This document specifies an implementation-oriented PostgreSQL physical design baseline translated from the Round 1.1 logical model. It does **not** create executable DDL, migration scripts, database objects, policies, roles, grants, triggers, functions, procedures, ORM models, application code, or deployment artifacts. No proposed design element is approved, implemented, validated, or production-ready.

**Baseline:** `audit/postgresql-round1-1-publication` commit `c433fe897d1922c9e154a19b5646c99c3ec6d73d` (`design/postgresql-round2-physical-schema` working branch). **ADR 0006 remains Proposed.** Proposed/Deferred/Open decisions are not promoted to Approved.

## 1. Purpose, scope, and authoritative baseline

This document defines the proposed PostgreSQL physical schema organization, logical-to-physical entity mapping, table and column specifications, key strategy, constraints, and relational integrity design for CARES Round 2. It covers **all Round 1.1 logical catalogue entities and relationships**, including entities simplified or omitted from logical ERDs, without omission.

**Sources inspected (actual repository documents):** [docs/POSTGRESQL_LOGICAL_DATA_MODEL.md](./POSTGRESQL_LOGICAL_DATA_MODEL.md), [docs/POSTGRESQL_LOGICAL_ERD.md](./POSTGRESQL_LOGICAL_ERD.md), [docs/POSTGRESQL_TRANSACTION_BOUNDARIES.md](./POSTGRESQL_TRANSACTION_BOUNDARIES.md), [docs/POSTGRESQL_SCHEMA_OPEN_DECISIONS.md](./POSTGRESQL_SCHEMA_OPEN_DECISIONS.md), [docs/POSTGRESQL_LOGICAL_MODEL_ROUND1_1_CHANGELOG.md](./POSTGRESQL_LOGICAL_MODEL_ROUND1_1_CHANGELOG.md), [docs/POSTGRESQL_LOGICAL_MODEL_ROUND1_1_FINAL_AUDIT.md](./POSTGRESQL_LOGICAL_MODEL_ROUND1_1_FINAL_AUDIT.md), [docs/DATA_ARCHITECTURE.md](./DATA_ARCHITECTURE.md), [docs/SECURITY_ARCHITECTURE.md](./SECURITY_ARCHITECTURE.md), [docs/POSTGRESQL_TECHNICAL_DECISIONS.md](./POSTGRESQL_TECHNICAL_DECISIONS.md), [docs/adr/0003-device-identity-and-asset-licensing.md](./adr/0003-device-identity-and-asset-licensing.md), [docs/adr/0005-event-processing-and-broker-evolution.md](./adr/0005-event-processing-and-broker-evolution.md), [docs/adr/0006-atomic-per-tenant-asset-licensing.md](./adr/0006-atomic-per-tenant-asset-licensing.md), [docs/PROJECT_STATUS.md](./PROJECT_STATUS.md), architecture cross-document consistency/reconciliation documents, and existing export/packaging conventions.

**Companion Round 2 documents:** [POSTGRESQL_PHYSICAL_ERD.md](./POSTGRESQL_PHYSICAL_ERD.md), [POSTGRESQL_INDEX_STRATEGY.md](./POSTGRESQL_INDEX_STRATEGY.md), [POSTGRESQL_RLS_AND_TENANT_ISOLATION_DESIGN.md](./POSTGRESQL_RLS_AND_TENANT_ISOLATION_DESIGN.md), [POSTGRESQL_PHYSICAL_TRANSACTION_DESIGN.md](./POSTGRESQL_PHYSICAL_TRANSACTION_DESIGN.md), [POSTGRESQL_DATA_LIFECYCLE_AND_RETENTION.md](./POSTGRESQL_DATA_LIFECYCLE_AND_RETENTION.md), [POSTGRESQL_PHYSICAL_SCHEMA_OPEN_DECISIONS.md](./POSTGRESQL_PHYSICAL_SCHEMA_OPEN_DECISIONS.md), [POSTGRESQL_PHYSICAL_SCHEMA_ROUND2_CHANGELOG.md](./POSTGRESQL_PHYSICAL_SCHEMA_ROUND2_CHANGELOG.md), [POSTGRESQL_PHYSICAL_SCHEMA_ROUND2_FINAL_REVIEW.md](./POSTGRESQL_PHYSICAL_SCHEMA_ROUND2_FINAL_REVIEW.md).

## 2. Architectural invariants (preserved)

- Modular monolith; PostgreSQL primary relational system of record; no Kafka/NATS/ClickHouse/Kubernetes or additional infrastructure introduced without measured requirements and explicit decisions.
- Core CARES platform remains functional without MELIRA AI.
- Strict multi-tenancy: tenant authority from trusted, verified, transaction-bound context only (never client-supplied tenant IDs; never user-settable PostgreSQL GUC authorization). RLS defense in depth, not sufficient alone; application authorization required. Prevent cross-tenant reads/writes/joins/references/indirect leakage.
- One unique monitored device = one licensed asset per tenant; multiple data sources reporting same device must not create multiple licensed assets; equal device-type licensing weight; licensing separate from technical resource quotas.
- External AI SaaS only for MELIRA; explicit provider selection; no silent failover/automatic transfer; AI interaction auditing and data governance preserved.
- Round 1.1 semantics preserved: authoritative `asset_data_source` binding ownership of immutable `source_device_key_id` (OD-002 Proposed/open), explicit idempotency semantics (OD-008 Proposed/open), correct event dedup namespaces (OD-013 Proposed/open/partial), no exactly-once external delivery, typed relational lineage (no polymorphic `from_asset_or_op_ref`).
- Existing ADR statuses preserved; **ADR 0006 remains Proposed**. Established ten-phase product roadmap unchanged.

## 3. Schema organization (Section A)

### 3.1 Proposed schema namespaces and domain boundaries

| Schema | Purpose | Ownership (proposed role) | Tenant scope | Rationale |
|---|---|---|---|---|
| `core` | Canonical tenant/access, assets, identity/licensing, subscriptions, lineage, lifecycle, and tenant configuration records | controlled schema owner / migration role only (no runtime ownership) | Mixed: tenant root/global identity/support context plus tenant-owned tables | Consolidates system-of-record entities with strong relational integrity and shared conventions; avoids premature fragmentation. |
| `ingest` | Event receipts, security events, schema references, and ingestion-related idempotency artifacts | controlled schema owner / migration role only | Tenant-owned (except global schema reference catalog if global) | Separates high-volume ingestion/event storage and future partitioning/retention concerns from lower-churn core entities while preserving FK integrity where justified. |
| `processing` | Outbox messages/attempts and optional processing work items | controlled schema owner / migration role only | Tenant-owned or tenant-contextual | Isolates asynchronous coordination state, claim/lease behavior, and cleanup/retention from core domain tables. |
| `audit_evidence` | Operational/security audit, forensic evidence metadata, custody/version/transition records, AI interaction audit | controlled schema owner / migration role only | Tenant-owned or scope-dependent (explicit per table) | Groups append-oriented/audit-evidence records with stricter lifecycle, retention, and access-control requirements. |
| `integration_ai` | Data sources, integration configuration, AI provider/config/consent/secret-reference/budget records | controlled schema owner / migration role only | Tenant-owned unless explicitly global | Separates connector and external-provider governance metadata from canonical asset/event domains. |
| `soc` | Alerts, incident cases, detection rules/versions, vulnerability findings, threat intelligence references, inventory observations | controlled schema owner / migration role only | Tenant-owned except explicitly global reference catalogs | Groups SOC operational entities with distinct query/lifecycle patterns. |
| `security_internal` | Protected verified-context/binding/authorization-helper backing structures if physically required (implementation-specific) | restricted security/schema owner only | Internal/control-plane | Keeps sensitive enforcement-support structures isolated from ordinary runtime DML paths. Not all logical entities map here; physical necessity is conditional (Proposed). |

**Platform-global vs tenant-scoped (proposed):** `core.tenant`, `core.external_identity_subject`, `core.role`, and global/shared catalogs such as `soc.threat_intelligence_reference` and optionally `ingest.event_schema_reference` are platform-global or catalog-scoped as specified per table. All other tenant-owned records carry `tenant_id` and must enforce tenant-consistent relationships and RLS predicates.

**Cross-schema foreign keys:** permitted where relational integrity is required (e.g. `ingest.event_receipt` → `integration_ai.data_source`, `core.asset`; `audit_evidence.ai_interaction_audit` correlation to `audit_evidence.audit_event`), provided tenant consistency is enforced by composite keys/constraints or equivalent mechanisms documented per relationship and by RLS posture. No unnecessary schema fragmentation is introduced.

**Naming conventions (proposed):** snake_case schemas/tables/columns/constraints/indexes; singular table names aligned to logical entities where practical (e.g. `core.asset`, `ingest.event_receipt`); constraint names `pk_*`, `uq_*`, `fk_*`, `ck_*`; index names `ix_*`/`uq_*` per index strategy. Final physical names may be adjusted during implementation planning if conventions require, with traceability preserved.

### 3.2 Data types and nullability conventions

| Convention | Proposed choice | Rationale / trade-offs |
|---|---|---|
| Primary identifiers | `uuid` (v4 or v7 per implementation decision; see key strategy) stored as PostgreSQL `uuid` | Stable, non-sequential-enumeration-friendly identifiers; globally unique within domain intent; indexing/storage trade-offs vs bigint must be measured (assumption). |
| Tenant key | `tenant_id uuid NOT NULL` on all tenant-owned tables (and in tenant-consistent composite uniqueness/FKs where required) | Enables tenant-inclusive integrity and RLS predicates; required for isolation and query scoping. |
| Timestamps | `timestamptz` for all persisted event/creation/update/effective/expiry times | Avoids timezone ambiguity; required for auditability and retention logic. |
| Booleans | `boolean` for explicit flags | Clear semantics; avoid tri-state unless NULL is meaningful and documented. |
| Enumerated states | **Constrained `text` with CHECK constraints or lookup tables** preferred over PostgreSQL native enums for evolving domain states | Native enums complicate value changes/migrations; lookup tables add joins but improve governance; physical choice is a bounded decision (see open decisions/review). Proposed baseline: constrained `text` + CHECK for initial design clarity unless strong stability/casting benefits justify enums. |
| Monetary/capacity counters | `integer`/`bigint` or `numeric` depending on semantics (counts/capacity use integer/bigint; monetary/accounting uses `numeric(p,s)` if modeled) | Precision and overflow considerations; exact commercial precision requires OD-003/OD-004 approval. |
| Short codes/names | `text` with CHECK/length constraints as needed (not unconstrained except justified) | Flexibility with validation; avoids unnecessary varchar micro-optimization. |
| Semi-structured payload/metadata | `jsonb` only for truly variable, document-like, or connector-specific structures with defined purpose and validation/query policy | Preserves relational integrity for core keys/relationships; JSONB indexing/size/validation trade-offs documented in Section J of lifecycle/design companion docs. |
| External references/secrets | `text` reference identifiers/URIs/ARN-like locators (never plaintext secrets) | Aligns with secret-manager/KMS boundary and ADR/SEC requirements. |
| Integrity hashes | fixed/known-length encoded `text` or `bytea` (implementation choice) with algorithm metadata | Supports evidence/integrity verification; representation deferred to implementation detail if bounded. |

**Shared columns convention (applied per table unless stated otherwise):**
- `created_at timestamptz NOT NULL` (record creation time in system-of-record context)
- `updated_at timestamptz NOT NULL` (last metadata/state update time; append-only/history tables may omit or set equal to `created_at` per table spec)
- `created_by_actor_id uuid NULL` / `updated_by_actor_id uuid NULL` (references authorized actor/subject or system actor representation where applicable)
- `correlation_id text NULL` and/or typed correlation references where needed for tracing (sensitive-content rules apply)
- `row_version bigint NOT NULL DEFAULT 1` (optional optimistic concurrency marker, proposed where update contention/version checks are useful)

Each table specification below explicitly states which shared columns apply and any deviations (e.g. append-only tables use immutable `recorded_at`/`created_at` without mutable `updated_at`).

### 3.3 Logical-to-physical entity mapping (complete)

| Logical entity | Proposed physical table | Representation | Notes |
|---|---|---|---|
| `tenant` | `core.tenant` | Separate table | Tenant isolation root; platform-scope record. |
| `external_identity_subject` | `core.external_identity_subject` | Separate table | Global identity principal. |
| `tenant_membership` | `core.tenant_membership` | Separate table | Tenant-scoped membership. |
| `role` | `core.role` | Separate table | Global or scoped catalog (Proposed). |
| `role_permission` | `core.role_permission` | Separate table | Canonical role→capability mapping. |
| `membership_role_assignment` | `core.membership_role_assignment` | Separate table | Membership→role assignment. |
| `support_access_grant` | `core.support_access_grant` | Separate table | Time-bound, scoped, auditable support grant. |
| `support_access_approval` | `core.support_access_approval` | Separate table | Conditional/policy-dependent approval record. |
| `tenant_configuration` | `core.tenant_configuration` | Separate table | Canonical tenant config/policy-version references. |
| `asset` | `core.asset` | Separate table | Canonical one-device-one-asset licensing anchor. |
| `data_source` | `integration_ai.data_source` | Separate table | Connector/source instance (not billable). |
| `asset_data_source` | `core.asset_data_source` | Separate table | **Authoritative stable source-device binding (Proposed, OD-002 open).** Owns immutable `source_device_key_id`. |
| `source_device_key` | `core.source_device_key` | Optional separate table (1:1 dependent projection) or represented by binding-owned attributes only | **Not authoritative if materialized**; must be 1:1, same lifecycle, no competing attributes. Default physical proposal: model as dependent table only if needed for clarity/constraints; otherwise binding-owned key columns remain authoritative (decision bounded, OD-002). |
| `source_device_fingerprint_alias` | `core.source_device_fingerprint_alias` | Separate table | Versioned lookup alias to stable binding identity. |
| `asset_identity_claim` | `core.asset_identity_claim` | Separate table | Provenance/observation record. |
| `identity_resolution_case` | `core.identity_resolution_case` | Separate table | Conflict/pending resolution workflow state. |
| `asset_lifecycle_event` | `core.asset_lifecycle_event` | Separate table | Append-oriented lifecycle history. |
| `asset_merge_operation` | `core.asset_merge_operation` | Separate table | Authorized merge operation record. |
| `asset_split_operation` | `core.asset_split_operation` | Separate table | Authorized split operation record. |
| `asset_lineage_link` | `core.asset_lineage_link` | Separate table | Typed relational lineage (no polymorphic ref). |
| `subscription_entitlement` | `core.subscription_entitlement` | Separate table | Commercial/licensing entitlement terms (semantics OD-001/003/004). |
| `tenant_license_usage_state` | `core.tenant_license_usage_state` | Separate table (materialized/authoritative state) | Counter semantics Proposed/open (OD-003/004). |
| `asset_license_event` | `core.asset_license_event` | Separate table | Append-oriented licensing history. |
| `identity_operation_idempotency_ledger` | `core.identity_operation_idempotency_ledger` | Separate table | Durable identity/licensing idempotency (OD-008 Proposed). |
| `asset_license_reservation` | `core.asset_license_reservation` | Separate table | Optional/policy-dependent reservation record (OD-003). |
| `asset_tombstone` | `core.asset_tombstone` | Separate table | Optional distinct terminal historical record; complements terminal lifecycle state. |
| `event_receipt` | `ingest.event_receipt` | Separate table | Durable ingestion idempotency/acceptance with explicit namespace (OD-013). |
| `security_event` | `ingest.security_event` | Separate table (partition candidate, deferred) | Normalized/queryable accepted event. |
| `event_schema_reference` | `ingest.event_schema_reference` | Separate table | Schema/version/normalization contract reference. |
| `outbox_message` | `processing.outbox_message` | Separate table | Durable async work intent/state. |
| `outbox_attempt` | `processing.outbox_attempt` | Separate table | Claim/delivery attempt, lease/fence, ambiguity history. |
| `processing_work_item` | `processing.processing_work_item` | Separate table (optional/non-core, Proposed) | Included in catalogue; must not compete with receipt/outbox truth. May remain unused/deferred in implementation. |
| `audit_event` | `audit_evidence.audit_event` | Separate table | Operational/security audit metadata. |
| `forensic_evidence_record` | `audit_evidence.forensic_evidence_record` | Separate table | Evidence metadata/provenance/state. |
| `evidence_object_version` | `audit_evidence.evidence_object_version` | Separate table | Immutable object/version reference metadata. |
| `evidence_custody_event` | `audit_evidence.evidence_custody_event` | Separate table | Append-only custody history. |
| `evidence_transition_authorization` | `audit_evidence.evidence_transition_authorization` | Separate table | Controlled transition approval/authorization record. |
| `tenant_ai_provider_configuration` | `integration_ai.tenant_ai_provider_configuration` | Separate table | Explicit external provider/model/region selection (no secrets). |
| `ai_provider_secret_reference` | `integration_ai.ai_provider_secret_reference` | Separate table | External secret-manager/KMS reference only. |
| `ai_provider_policy_consent_reference` | `integration_ai.ai_provider_policy_consent_reference` | Separate table | Consent/policy/terms references. |
| `ai_usage_budget_accounting` | `integration_ai.ai_usage_budget_accounting` | Separate table | Usage/budget accounting (policy open). |
| `ai_interaction_audit` | `audit_evidence.ai_interaction_audit` | Separate table | Specialized AI/privacy/provider audit, correlatable with `audit_event`. |
| `alert` | `soc.alert` | Separate table | Detection-generated alert. |
| `incident_case` | `soc.incident_case` | Separate table | Investigation/response case container. |
| `detection_rule` | `soc.detection_rule` | Separate table | Rule definition metadata (tenant-owned or managed catalog scope Proposed). |
| `detection_rule_version` | `soc.detection_rule_version` | Separate table | Immutable/versioned rule snapshot. |
| `vulnerability_finding` | `soc.vulnerability_finding` | Separate table | Vulnerability/exposure finding. |
| `threat_intelligence_reference` | `soc.threat_intelligence_reference` | Separate table | Global/shared reference catalog with tenant usage linkage rules. |
| `asset_inventory_observation` | `soc.asset_inventory_observation` | Separate table | Point-in-time inventory observation/snapshot. |
| `integration_configuration` | `integration_ai.integration_configuration` | Separate table | Tenant-scoped integration settings + secret references. |

**Traceability note:** every logical entity above is represented as a proposed physical table or explicitly bounded as an optional dependent projection (`source_device_key`) / optional non-core table (`processing_work_item`) with documented rationale; no logical catalogue entity is omitted.


## 4. Primary key and identity strategy (Section C)

| Topic | Proposed decision | Rationale | Trade-offs / operational implications | Open dependencies |
|---|---|---|---|---|
| Surrogate primary keys | Use `uuid` PKs (`*_id`) for most entities/tables, including `core.tenant`, `core.asset`, binding/receipt/ledger/outbox/audit/evidence records | Stable identifiers suitable for distributed/service boundaries, reduce enumeration risk, simplify immutable references and lineage; align with existing logical `uuid` identifiers | Larger/wider indexes and FKs than bigint; random UUIDv4 can increase B-tree locality pressure (UUIDv7/time-ordered variant may mitigate, but requires implementation choice/validation). | UUID version/ordering choice is a bounded implementation-planning detail. |
| Canonical asset identity | `core.asset.asset_id uuid` is the immutable, tenant-scoped canonical monitored-device/licensing identity (non-reusable). A separate immutable canonical UUID attribute may be stored if distinct from PK, but default proposal: PK is canonical identity | Satisfies one-device-one-asset and non-reuse requirements; simplifies lineage/history references | Requires lifecycle/tombstone controls to prevent reuse and preserve history | ADR 0006 Proposed; OD-001/003/004 affect accounting semantics, not canonical non-reuse. |
| Stable source-device binding identity | `core.asset_data_source.source_device_key_id uuid NOT NULL` is immutable and owned by the authoritative binding row (Proposed, OD-002). Uniqueness scoped to prevent competing bindings per approved context | Single source of truth for binding identity; supports alias resolution and event dedup namespace derivation | Physical uniqueness dimensions depend on approved binding rules/connector behavior | **OD-002 approval required**. |
| Dependent `source_device_key` projection | If materialized, `core.source_device_key.source_device_key_id` PK equals/uniquely maps to binding-owned key with 1:1 FK/unique constraint to `core.asset_data_source` and identical lifecycle; no independent mutable authority | Allows explicit table if useful for constraints/readability without competing truth | Extra join/table maintenance; risk of divergence if not strictly constrained (must be prevented by design/tests) | OD-002. |
| Tenant-aware uniqueness | Tenant-owned entities include `tenant_id` in PK only where composite PK is justified; otherwise enforce tenant-scoped uniqueness via unique indexes/constraints on (`tenant_id`, business key) and tenant-consistent FKs | Supports multi-tenant isolation, partitioning flexibility (future), and cross-tenant collision prevention | Composite PKs widen child FKs; composite unique constraints + surrogate PK often balance integrity and ergonomics | Physical FK composition choices documented per table. |
| Natural/alternate keys | Define alternate unique keys for business/idempotency identities: e.g. (`tenant_id`,`operation_type`,`idempotency_key`) for ledger, explicit dedup namespace key for `event_receipt`, (`tenant_id`,`issuer`,`subject`) or equivalent for external subject mapping, binding uniqueness as approved | Enforces correctness under retries/concurrency and integration lookups | Additional index/write cost; must reflect approved semantics | OD-008, OD-013, OD-002. |
| Stable external identifiers | Store external provider/connector/IdP identifiers as attributes with uniqueness scoped appropriately; do not replace internal surrogate PKs except justified | Preserves internal referential stability and supports reconciliation/rotation | Requires mapping indexes and provenance | Connector-specific details open where noted. |
| Immutable vs mutable identifiers | PKs and canonical/binding/ledger identity keys immutable after creation; mutable business attributes versioned via history/transition records where required (aliases, evidence versions, rule versions) | Supports auditability, lineage, and replay correctness | More tables/rows; requires controlled transition operations | Merge/split/lifecycle rules per operations. |
| Referential integrity during identity reconciliation | Use typed FKs, staged states (`identity_resolution_case`, claims), and transactional reassignment (merge/split ops) rather than mutable ambiguous references; losing assets become terminal/tombstoned, IDs never reused | Prevents dangling/ambiguous identity graphs and licensing corruption | Complex transactional coordination; some invariants may need DEFERRABLE constraints or procedural enforcement (documented) | OD-005, OD-003/004. |

**Multi-tenancy/indexing/ingestion implications (proposed):** include `tenant_id` as leading column in most tenant-scoped lookup/uniqueness indexes and consider tenant-partition-aligned access patterns later; avoid cross-tenant global uniqueness on tenant-owned business keys; ingestion/idempotency tables require contention-aware unique constraints and may benefit from time-ordered PK/insert patterns (assumption, to validate).

## 5. Constraints and relational integrity (Section D)

### 5.1 Constraint classes and enforcement principles

| Class | Proposed use | Enforcement notes |
|---|---|---|
| Primary keys | Every table has an explicit PK | Surrogate UUID PK default; composite PK only where justified. |
| Foreign keys | All relationship references use typed FKs to existing proposed keys | Prefer same-type UUID FKs; include `tenant_id` consistency mechanisms for tenant-owned relationships (composite FK where parent uniqueness includes tenant, or supporting unique constraints/checks). |
| Unique constraints/indexes | Enforce canonical identity, binding, alias, dedup/idempotency, and business-key invariants | Partial unique indexes may be proposed for state-specific uniqueness (e.g. active bindings) where semantics require; exact predicates depend on approved states. |
| Check constraints | Enforce domain/state validity, non-negative counters (where applicable), mutually exclusive typed lineage references, and basic structural invariants | Complex temporal/overlap rules may require triggers/procedures or application enforcement with explicit risk documentation (deferred to implementation review). |
| Referential actions | `ON DELETE RESTRICT`/`NO ACTION` default for integrity-critical records; `CASCADE` only for tightly owned dependent rows where safe and approved; `SET NULL` only for optional references with clear semantics | Deletion/retention/legal-hold constraints may override cascade behavior (see lifecycle doc). |
| Nullable relationships | Nullable FKs only where relationship is genuinely optional/unresolved (e.g. pending claims, optional asset attribution) | Nullability must not weaken tenant or identity integrity. |

### 5.2 Tenant consistency across related rows

- **Rule:** for tenant-owned child rows, `tenant_id` must equal the referenced tenant-owned parent’s `tenant_id`. Proposed enforcement mechanisms (to be selected/finalized in implementation design): (1) composite FKs referencing `(tenant_id, id)` parent unique keys, (2) composite PK/unique keys on parents enabling tenant-inclusive references, and/or (3) validated triggers/checks where composite FK is impractical.
- **Limitation:** single-column FKs to surrogate PKs do not by themselves prove same-tenant ownership; therefore tenant-consistent composite keys/constraints are **required design intent** for critical tenant-owned relationships, with any exception explicitly documented and risk-assessed.
- Global/catalog references (e.g. `soc.threat_intelligence_reference`, `core.role` if global) must not create cross-tenant data leakage paths; tenant usage/link tables carry `tenant_id` and FK to global ID.

### 5.3 Asset lineage integrity (Round 1.1 correction preserved)

- `core.asset_lineage_link` uses typed `from_asset_id` and `to_asset_id` FKs to `core.asset`, plus nullable typed `merge_operation_id` FK to `core.asset_merge_operation` and `split_operation_id` FK to `core.asset_split_operation` according to `link_type`.
- **Proposed structural invariant:** exactly the operation FK appropriate to `link_type` is non-null and the other is null (mutual exclusivity), all referenced rows share the same `tenant_id`, and canonical asset IDs are never reused.
- This replaces and prohibits the prior polymorphic `from_asset_or_op_ref` design.

### 5.4 Merge/split, lifecycle, and historical records

- `asset_merge_operation` and `asset_split_operation` are authoritative operation records; losing/source/result asset state transitions recorded in lifecycle/license/lineage/tombstone records within controlled transactions.
- Terminal historical records (`asset_tombstone`, custody/evidence history, audit history) are append-only or immutable by policy intent; destructive deletion constrained by retention/legal hold/evidence preservation rules.
- Circular FK dependencies should be avoided; where unavoidable, use deferrable constraints or staged insertion patterns (documented as implementation concern if identified).

### 5.5 Application-only enforcement (risk transparency)

- Some invariants cannot be fully enforced by ordinary FKs/checks alone (e.g. complex quota accounting equations pending OD-003/004, certain temporal overlap semantics, external object existence, cryptographic verification outcomes, "exactly one active canonical resolution" under all workflow states). Where application/service enforcement is required, the design must still use all feasible DB constraints and transactions; residual reliance on application logic is a **documented risk** requiring verification tests and, where appropriate, compensating reconciliation/monitoring.

## 6. Physical entity and table definitions (Section B)

**Specification notes:** "Shared columns" refers to the convention in §3.2 unless a table states deviations. Data types are proposed PostgreSQL types. `tenant ownership semantics` distinguishes tenant-owned, platform-global, and scope-dependent records. All tenant-owned tables are expected to participate in RLS defense-in-depth (see RLS design document). Sensitive-data classification is indicative (proposed) and subject to privacy/security review.


### 6.1 Core and tenant/access domain

#### `core.tenant`
- **Logical entity:** `tenant`
- **Business purpose:** Tenant isolation and authorization root; canonical tenant identity and lifecycle.
- **Primary key:** `tenant_id uuid`
- **Candidate alternate keys:** `tenant_slug` or external tenant identifier (if assigned) unique when present.
- **Tenant ownership semantics:** Platform-global/root record representing the tenant itself.
- **Lifecycle and deletion behavior:** Lifecycle states managed explicitly (e.g. provisioning/active/suspended/deprovisioned/archived); hard deletion restricted by retention, legal, audit/evidence, and offboarding controls. No silent deletion.
- **Audit requirements:** Tenant creation/state changes/configuration-affecting actions auditable via `audit_evidence.audit_event`.
- **Sensitive-data classification:** Operational/business-sensitive tenant metadata; PII limited to administrative contacts if stored (prefer separate controlled records if needed).
- **Shared columns:** `created_at timestamptz NOT NULL`, `updated_at timestamptz NOT NULL`, `created_by_actor_id uuid NULL`, `updated_by_actor_id uuid NULL`, `row_version bigint NOT NULL DEFAULT 1`.

| Column | PostgreSQL type | Nullability | Default | Description / constraints role |
|---|---|---|---|---|
| `tenant_id` | `uuid` | NOT NULL | generated by application/service | Canonical tenant identifier (PK). |
| `tenant_name` | `text` | NOT NULL | none | Human-readable tenant name. |
| `tenant_slug` | `text` | NULL | null | Optional stable URL-safe/external reference; unique when not null. |
| `tenant_status` | `text` | NOT NULL | `'provisioning'` (proposed) | Lifecycle/status; CHECK constrained to approved states. |
| `status_reason` | `text` | NULL | null | Optional operator/system reason for current status. |
| `activated_at` | `timestamptz` | NULL | null | Time tenant became active. |
| `suspended_at` | `timestamptz` | NULL | null | Time tenant suspended. |
| `deprovisioned_at` | `timestamptz` | NULL | null | Time deprovisioning completed/requested per policy. |
| `metadata` | `jsonb` | NULL | null | Limited non-sensitive administrative metadata only if justified; must not store secrets/credentials/authorization authority. |

- **Foreign-key relationships:** Referenced by nearly all tenant-owned tables via `tenant_id`.
- **Unique constraints:** `uq_tenant_slug` on (`tenant_slug`) where not null (partial unique proposed).
- **Check constraints (proposed):** `tenant_status` in allowed set; temporal consistency checks (e.g. `deprovisioned_at` only with appropriate status) where enforceable.

#### `core.external_identity_subject`
- **Logical entity:** `external_identity_subject`
- **Business purpose:** Represents a human or non-human principal authenticated by an external IdP/identity source.
- **Primary key:** `external_identity_subject_id uuid`
- **Candidate alternate keys:** (`issuer`, `subject`) unique; optional stable external principal key per issuer.
- **Tenant ownership semantics:** Platform-global identity record; tenant access expressed through `core.tenant_membership`.
- **Lifecycle and deletion behavior:** Active/disabled/merged-by-identity-provider semantics controlled by administrative processes; deletion restricted for audit traceability (prefer disable/anonymization policy subject to privacy/legal review).
- **Audit requirements:** Creation, linking, status, and attribute-governance changes auditable.
- **Sensitive-data classification:** Identity/PII-sensitive (issuer, subject, display identifiers, emails if stored); minimize stored attributes.
- **Shared columns:** Standard shared columns.

| Column | PostgreSQL type | Nullability | Default | Description / constraints role |
|---|---|---|---|---|
| `external_identity_subject_id` | `uuid` | NOT NULL | generated | PK. |
| `issuer` | `text` | NOT NULL | none | External IdP/issuer identifier. |
| `subject` | `text` | NOT NULL | none | Issuer-scoped subject identifier. |
| `principal_type` | `text` | NOT NULL | none | e.g. `human`, `service`, `agent` (CHECK constrained). |
| `display_name` | `text` | NULL | null | Optional display label. |
| `primary_email` | `text` | NULL | null | Optional; minimized PII. |
| `subject_status` | `text` | NOT NULL | `'active'` | Status; CHECK constrained. |
| `last_seen_at` | `timestamptz` | NULL | null | Last authenticated/observed time. |

- **Foreign-key relationships:** Referenced by `core.tenant_membership`, support/access/audit actor references as applicable.
- **Unique constraints:** `uq_external_identity_subject_issuer_subject` on (`issuer`, `subject`).
- **Check constraints (proposed):** non-empty `issuer`/`subject`; valid `principal_type` and `subject_status`.

#### `core.tenant_membership`
- **Logical entity:** `tenant_membership`
- **Business purpose:** Authorizes an external identity subject within a specific tenant scope.
- **Primary key:** `tenant_membership_id uuid`
- **Candidate alternate keys:** (`tenant_id`, `external_identity_subject_id`) unique for active/current membership model (exact temporal model proposed).
- **Tenant ownership semantics:** Tenant-owned.
- **Lifecycle and deletion behavior:** Invitation/active/suspended/revoked/expired states; historical records retained per audit policy.
- **Audit requirements:** Grant/revoke/suspend/role-scope changes auditable.
- **Sensitive-data classification:** Identity/access-sensitive.
- **Shared columns:** Standard shared columns.

| Column | PostgreSQL type | Nullability | Default | Description / constraints role |
|---|---|---|---|---|
| `tenant_membership_id` | `uuid` | NOT NULL | generated | PK. |
| `tenant_id` | `uuid` | NOT NULL | none | FK to `core.tenant`. |
| `external_identity_subject_id` | `uuid` | NOT NULL | none | FK to `core.external_identity_subject`. |
| `membership_status` | `text` | NOT NULL | `'active'` (proposed) | CHECK constrained. |
| `joined_at` | `timestamptz` | NULL | null | Effective membership start. |
| `revoked_at` | `timestamptz` | NULL | null | Revocation time. |
| `revocation_reason` | `text` | NULL | null | Optional reason. |

- **Foreign-key relationships:** FK (`tenant_id`)→`core.tenant`; FK (`external_identity_subject_id`)→`core.external_identity_subject`; referenced by `core.membership_role_assignment`, support grants/approvals context as applicable.
- **Unique constraints:** proposed `uq_tenant_membership_subject` on (`tenant_id`, `external_identity_subject_id`) (may be partial by status depending on final semantics).
- **Check constraints (proposed):** valid status; revocation timestamp consistency.

#### `core.role`
- **Logical entity:** `role`
- **Business purpose:** Named role grouping permissions/capabilities.
- **Primary key:** `role_id uuid`
- **Candidate alternate keys:** (`role_scope`, `role_code`) or (`tenant_id`, `role_code`) unique depending on global vs tenant-defined roles (proposed).
- **Tenant ownership semantics:** Proposed global/system roles plus optional tenant-defined roles (`tenant_id` nullable/global marker) — exact model open to implementation governance.
- **Lifecycle and deletion behavior:** Versioning/replacement preferred over destructive deletion if referenced.
- **Audit requirements:** Role definition changes auditable.
- **Sensitive-data classification:** Access-control metadata (sensitive).
- **Shared columns:** Standard shared columns.

| Column | PostgreSQL type | Nullability | Default | Description / constraints role |
|---|---|---|---|---|
| `role_id` | `uuid` | NOT NULL | generated | PK. |
| `tenant_id` | `uuid` | NULL | null | NULL for global/system role; set for tenant-defined custom role (proposed). |
| `role_code` | `text` | NOT NULL | none | Stable role identifier. |
| `role_name` | `text` | NOT NULL | none | Display name. |
| `role_scope` | `text` | NOT NULL | none | e.g. `system`, `tenant`, `support` (CHECK constrained). |
| `description` | `text` | NULL | null | Purpose description. |
| `is_system_defined` | `boolean` | NOT NULL | false | Protects system roles from tenant mutation. |

- **Foreign-key relationships:** optional FK (`tenant_id`)→`core.tenant`; referenced by `core.role_permission` and `core.membership_role_assignment`.
- **Unique constraints:** proposed uniqueness on (`tenant_id`, `role_code`) treating NULL tenant distinctly per chosen rule, or equivalent partial uniques.
- **Check constraints (proposed):** valid scope; system roles have NULL `tenant_id`.

#### `core.role_permission`
- **Logical entity:** `role_permission`
- **Business purpose:** Canonical mapping of a role to granted permissions/capabilities (distinct from membership assignment).
- **Primary key:** `role_permission_id uuid` (surrogate) or composite (`role_id`, `permission_code`).
- **Candidate alternate keys:** (`role_id`, `permission_code`) unique.
- **Tenant ownership semantics:** Follows role scope; if role is global, mapping is global.
- **Lifecycle and deletion behavior:** Mutable mapping by controlled admin path, auditable; remove rows when permission revoked from role.
- **Audit requirements:** Permission grant/revoke auditable.
- **Sensitive-data classification:** Access-control metadata.
- **Shared columns:** Standard shared columns.

| Column | PostgreSQL type | Nullability | Default | Description / constraints role |
|---|---|---|---|---|
| `role_permission_id` | `uuid` | NOT NULL | generated | PK (proposed surrogate). |
| `role_id` | `uuid` | NOT NULL | none | FK to `core.role`. |
| `permission_code` | `text` | NOT NULL | none | Capability/permission identifier. |
| `effect` | `text` | NOT NULL | `'allow'` | e.g. allow/deny if deny model used (proposed CHECK). |
| `resource_scope` | `text` | NULL | null | Optional scope qualifier. |

- **Foreign-key relationships:** FK (`role_id`)→`core.role`.
- **Unique constraints:** `uq_role_permission` on (`role_id`, `permission_code`, COALESCE(`resource_scope`,'')) or explicit rule.
- **Check constraints (proposed):** valid `effect`.

#### `core.membership_role_assignment`
- **Logical entity:** `membership_role_assignment`
- **Business purpose:** Assigns a role to a tenant membership (distinct from role-permission definitions).
- **Primary key:** `membership_role_assignment_id uuid`
- **Candidate alternate keys:** (`tenant_membership_id`, `role_id`) unique for active assignment model.
- **Tenant ownership semantics:** Tenant-owned (must align with membership tenant and role scope rules).
- **Lifecycle and deletion behavior:** Time-bounded/effective-dated assignments possible; revoke/end rather than erase history where audit required.
- **Audit requirements:** Assignment/revocation auditable.
- **Sensitive-data classification:** Access-control metadata.
- **Shared columns:** Standard shared columns.

| Column | PostgreSQL type | Nullability | Default | Description / constraints role |
|---|---|---|---|---|
| `membership_role_assignment_id` | `uuid` | NOT NULL | generated | PK. |
| `tenant_id` | `uuid` | NOT NULL | none | Tenant scope for RLS/consistency. |
| `tenant_membership_id` | `uuid` | NOT NULL | none | FK to `core.tenant_membership`. |
| `role_id` | `uuid` | NOT NULL | none | FK to `core.role`. |
| `assignment_status` | `text` | NOT NULL | `'active'` | CHECK constrained. |
| `effective_from` | `timestamptz` | NOT NULL | `now()` (proposed at insert) | Start of effectiveness. |
| `effective_to` | `timestamptz` | NULL | null | End/revocation time. |

- **Foreign-key relationships:** FKs to `core.tenant`, `core.tenant_membership`, `core.role`; tenant consistency with membership required.
- **Unique constraints:** proposed `uq_membership_role_active` on (`tenant_membership_id`, `role_id`) possibly partial.
- **Check constraints (proposed):** `effective_to` null or >= `effective_from`.

#### `core.support_access_grant`
- **Logical entity:** `support_access_grant`
- **Business purpose:** Explicit, time-bound, scoped, reasoned, auditable support access grant (not blanket membership, not BYPASSRLS).
- **Primary key:** `support_access_grant_id uuid`
- **Candidate alternate keys:** none required beyond PK; optional external ticket/reference unique per policy.
- **Tenant ownership semantics:** Tenant-contextual/scope record (target tenant explicit).
- **Lifecycle and deletion behavior:** Requested/approved/active/expired/revoked/denied states; retained for audit.
- **Audit requirements:** Full lifecycle, approvals, activations, and uses auditable.
- **Sensitive-data classification:** Highly sensitive authorization/audit metadata.
- **Shared columns:** Standard shared columns.

| Column | PostgreSQL type | Nullability | Default | Description / constraints role |
|---|---|---|---|---|
| `support_access_grant_id` | `uuid` | NOT NULL | generated | PK. |
| `target_tenant_id` | `uuid` | NOT NULL | none | Tenant whose data/scope is accessed; FK to `core.tenant`. |
| `grantee_subject_id` | `uuid` | NOT NULL | none | Support principal; FK to `core.external_identity_subject`. |
| `requested_by_subject_id` | `uuid` | NULL | null | Requestor principal. |
| `grant_status` | `text` | NOT NULL | `'requested'` | CHECK constrained. |
| `access_scope` | `jsonb` | NOT NULL | none | Structured, minimal scope definition (resources/actions/constraints); purpose and validation required. |
| `reason` | `text` | NOT NULL | none | Justification/ticket context. |
| `starts_at` | `timestamptz` | NOT NULL | none | Grant validity start. |
| `expires_at` | `timestamptz` | NOT NULL | none | Grant validity end (mandatory, time-bound). |
| `revoked_at` | `timestamptz` | NULL | null | Revocation time. |

- **Foreign-key relationships:** FKs to `core.tenant` (target), `core.external_identity_subject` (grantee/requestor).
- **Unique constraints:** none mandatory.
- **Check constraints (proposed):** `expires_at` > `starts_at`; status consistency with revocation/approval.

#### `core.support_access_approval`
- **Logical entity:** `support_access_approval`
- **Business purpose:** Conditional/policy-dependent approval record for support access grants.
- **Primary key:** `support_access_approval_id uuid`
- **Candidate alternate keys:** (`support_access_grant_id`, `approval_step`, `approver_subject_id`) or policy-defined uniqueness.
- **Tenant ownership semantics:** Follows grant/target tenant context.
- **Lifecycle and deletion behavior:** Immutable decision records preferred; retained for audit.
- **Audit requirements:** Approvals/denials fully auditable.
- **Sensitive-data classification:** Highly sensitive authorization metadata.
- **Shared columns:** `created_at`, `updated_at` (or immutable `decided_at`), actor columns.

| Column | PostgreSQL type | Nullability | Default | Description / constraints role |
|---|---|---|---|---|
| `support_access_approval_id` | `uuid` | NOT NULL | generated | PK. |
| `support_access_grant_id` | `uuid` | NOT NULL | none | FK to `core.support_access_grant`. |
| `target_tenant_id` | `uuid` | NOT NULL | none | Tenant consistency. |
| `approver_subject_id` | `uuid` | NULL | null | Approver principal (nullable for automated/policy decisions if explicitly modeled). |
| `approval_step` | `text` | NOT NULL | `'primary'` | Step/type identifier. |
| `decision` | `text` | NOT NULL | none | `approved`/`denied`/`pending` CHECK constrained. |
| `decision_reason` | `text` | NULL | null | Rationale. |
| `decided_at` | `timestamptz` | NULL | null | Decision timestamp. |

- **Foreign-key relationships:** FK to `core.support_access_grant`, `core.tenant`, `core.external_identity_subject`.
- **Unique constraints:** proposed uniqueness per grant/step/approver as policy requires.
- **Check constraints (proposed):** valid decision values.

#### `core.tenant_configuration`
- **Logical entity:** `tenant_configuration`
- **Business purpose:** Canonical tenant-scoped configuration and policy-version references (not AI-provider-specific canonical record).
- **Primary key:** `tenant_configuration_id uuid`
- **Candidate alternate keys:** (`tenant_id`, `config_domain`, `effective_from`) or (`tenant_id`, `config_domain`, `version`) unique.
- **Tenant ownership semantics:** Tenant-owned.
- **Lifecycle and deletion behavior:** Versioned/effective-dated; supersede rather than overwrite when history required.
- **Audit requirements:** Configuration changes auditable with actor/reason/correlation.
- **Sensitive-data classification:** May contain sensitive policy settings; no secrets.
- **Shared columns:** Standard shared columns.

| Column | PostgreSQL type | Nullability | Default | Description / constraints role |
|---|---|---|---|---|
| `tenant_configuration_id` | `uuid` | NOT NULL | generated | PK. |
| `tenant_id` | `uuid` | NOT NULL | none | FK to `core.tenant`. |
| `config_domain` | `text` | NOT NULL | none | Domain/key (e.g. security, retention policy reference, feature flags namespace) CHECK/validated. |
| `config_version` | `integer` | NOT NULL | 1 | Monotonic or scoped version. |
| `config_status` | `text` | NOT NULL | `'active'` | `draft/active/superseded/revoked` proposed. |
| `effective_from` | `timestamptz` | NOT NULL | none | Effective start. |
| `effective_to` | `timestamptz` | NULL | null | Effective end. |
| `config_body` | `jsonb` | NOT NULL | `'{}'::jsonb` | Structured config; schema/validation governed by application/policy; no secrets. |
| `source_reference` | `text` | NULL | null | Optional external/policy reference ID. |

- **Foreign-key relationships:** FK to `core.tenant`; referenced by other records by ID where version pinning is required.
- **Unique constraints:** proposed uniqueness on (`tenant_id`, `config_domain`, `config_version`).
- **Check constraints (proposed):** `config_version > 0`; effective window consistency.

### 6.2 Asset, identity, lineage, and licensing domain

#### `core.asset`
- **Logical entity:** `asset`
- **Business purpose:** Canonical tenant-scoped monitored-device identity and **one-device-one-licensed-asset** anchor.
- **Primary key:** `asset_id uuid`
- **Candidate alternate keys:** (`tenant_id`, `asset_id`) unique (supports tenant-consistent FKs); no reusable canonical business key.
- **Tenant ownership semantics:** Tenant-owned.
- **Lifecycle and deletion behavior:** Explicit lifecycle (e.g. candidate/active/suspended/deactivated/merged_away/split_replaced/terminal_tombstoned as applicable, Proposed); canonical IDs never reused; terminal state represented in history/tombstone rather than destructive erasure.
- **Audit requirements:** All lifecycle, identity, and licensing-impacting changes auditable.
- **Sensitive-data classification:** Asset identity and operational metadata; potentially sensitive depending on attributes.
- **Shared columns:** Standard shared columns.

| Column | PostgreSQL type | Nullability | Default | Description / constraints role |
|---|---|---|---|---|
| `asset_id` | `uuid` | NOT NULL | generated | PK; canonical non-reusable asset identity. |
| `tenant_id` | `uuid` | NOT NULL | none | FK to `core.tenant`. |
| `asset_display_name` | `text` | NULL | null | Optional human-readable label. |
| `asset_kind` | `text` | NOT NULL | none | Device/asset kind classification; equal licensing weight across device types. |
| `asset_status` | `text` | NOT NULL | `'candidate'` (proposed) | Lifecycle/status CHECK constrained. |
| `canonical_identity_state` | `text` | NOT NULL | `'unresolved'` (proposed) | Identity confidence/state indicator. |
| `first_seen_at` | `timestamptz` | NULL | null | First observation/enrollment time. |
| `last_seen_at` | `timestamptz` | NULL | null | Last observation time. |
| `deactivated_at` | `timestamptz` | NULL | null | Deactivation/removal effective time. |
| `terminal_reason` | `text` | NULL | null | Reason for terminal/merged/split state. |
| `attributes` | `jsonb` | NULL | null | Limited non-authoritative descriptive attributes; must not store authoritative identity/licensing truth except as explicitly designed references. |

- **Foreign-key relationships:** FK (`tenant_id`)→`core.tenant`; referenced by bindings, claims, receipts/events, lineage, license records, observations, findings, alerts/incidents as applicable.
- **Unique constraints:** `uq_asset_tenant_asset` on (`tenant_id`, `asset_id`) to support tenant-consistent composite FKs.
- **Check constraints (proposed):** valid status/state enums (constrained text); temporal consistency.

#### `integration_ai.data_source`
- **Logical entity:** `data_source`
- **Business purpose:** Tenant-scoped connector/source instance that may report one or many devices; **not a billable asset**.
- **Primary key:** `data_source_id uuid`
- **Candidate alternate keys:** (`tenant_id`, `source_code`) or (`tenant_id`, `external_source_identifier`) unique per policy.
- **Tenant ownership semantics:** Tenant-owned.
- **Lifecycle and deletion behavior:** Enabled/disabled/retired states; retained for provenance and historical receipts.
- **Audit requirements:** Configuration/status/credential-reference changes auditable.
- **Sensitive-data classification:** Integration metadata; may be sensitive; no credentials stored directly.
- **Shared columns:** Standard shared columns.

| Column | PostgreSQL type | Nullability | Default | Description / constraints role |
|---|---|---|---|---|
| `data_source_id` | `uuid` | NOT NULL | generated | PK. |
| `tenant_id` | `uuid` | NOT NULL | none | FK to `core.tenant`. |
| `source_type` | `text` | NOT NULL | none | Connector/integration type. |
| `source_name` | `text` | NOT NULL | none | Display/name. |
| `external_source_identifier` | `text` | NULL | null | Connector-side/source-system identifier. |
| `source_status` | `text` | NOT NULL | `'active'` | CHECK constrained. |
| `trust_level` | `text` | NULL | null | Optional trust/provenance classification. |
| `integration_configuration_id` | `uuid` | NULL | null | Optional FK to `integration_ai.integration_configuration`. |

- **Foreign-key relationships:** FK to `core.tenant`; optional FK to `integration_ai.integration_configuration`; referenced by `core.asset_data_source`, claims, observations, `ingest.event_receipt`.
- **Unique constraints:** proposed `uq_data_source_tenant_external` on (`tenant_id`, `external_source_identifier`) where not null; and/or `uq_data_source_tenant_name` policy-dependent.
- **Check constraints (proposed):** valid status.

#### `core.asset_data_source`
- **Logical entity:** `asset_data_source`
- **Business purpose:** **Authoritative stable source-device binding** between a canonical asset and a specific data source; owns immutable `source_device_key_id` (Round 1.1, OD-002 Proposed/open).
- **Primary key:** `asset_data_source_id uuid`
- **Candidate alternate keys:** (`tenant_id`, `source_device_key_id`) unique; (`tenant_id`, `data_source_id`, `source_local_device_identifier` or approved binding key) unique as applicable; one binding identity must not map to competing assets.
- **Tenant ownership semantics:** Tenant-owned.
- **Lifecycle and deletion behavior:** Binding states (active/inactive/conflicted/retired as proposed) with auditable transitions; immutable `source_device_key_id`; historical bindings retained.
- **Audit requirements:** Creation, reassignment attempts, conflict, deactivation, and key-related governance actions auditable.
- **Sensitive-data classification:** Device/source identity-sensitive.
- **Shared columns:** Standard shared columns.

| Column | PostgreSQL type | Nullability | Default | Description / constraints role |
|---|---|---|---|---|
| `asset_data_source_id` | `uuid` | NOT NULL | generated | PK. |
| `tenant_id` | `uuid` | NOT NULL | none | FK to `core.tenant`. |
| `asset_id` | `uuid` | NOT NULL | none | FK to canonical `core.asset`. |
| `data_source_id` | `uuid` | NOT NULL | none | FK to `integration_ai.data_source`. |
| `source_device_key_id` | `uuid` | NOT NULL | none | **Immutable authoritative binding-owned stable key** (Proposed, OD-002). |
| `source_local_device_identifier` | `text` | NULL | null | Source-local identifier if available; provenance only unless part of approved binding rule. |
| `binding_status` | `text` | NOT NULL | `'active'` | CHECK constrained. |
| `first_bound_at` | `timestamptz` | NOT NULL | `now()` proposed | Initial binding time. |
| `last_confirmed_at` | `timestamptz` | NULL | null | Last confirmation/observation. |
| `confidence_level` | `text` | NULL | null | Optional confidence/provenance classification. |

- **Foreign-key relationships:** FKs to `core.tenant`, `core.asset`, `integration_ai.data_source`; referenced by `core.source_device_key` (if materialized), `core.source_device_fingerprint_alias`, claims/cases/receipts as applicable.
- **Unique constraints:** proposed `uq_asset_data_source_tenant_source_device_key` on (`tenant_id`, `source_device_key_id`); additional binding uniqueness constraints per OD-002/implementation (e.g. prevent multiple active canonical bindings for same source-device identity context).
- **Check constraints (proposed):** valid binding status; non-null immutable key semantics enforced by update controls/application policy.

#### `core.source_device_key` (optional dependent projection)
- **Logical entity:** `source_device_key`
- **Business purpose:** Optional 1:1 dependent projection of the authoritative binding-owned `source_device_key_id`; **not a competing identity authority**.
- **Primary key:** `source_device_key_id uuid` (same value as `core.asset_data_source.source_device_key_id`)
- **Candidate alternate keys:** 1:1 enforced via PK/FK to binding.
- **Tenant ownership semantics:** Tenant-owned (derived from binding).
- **Lifecycle and deletion behavior:** Created/retired in lockstep with authoritative binding; cannot outlive or diverge from binding.
- **Audit requirements:** Materialization/changes (if any) auditable; normally immutable.
- **Sensitive-data classification:** Device identity-sensitive.
- **Shared columns:** Minimal `created_at`, `updated_at` (or immutable timestamps) as needed.

| Column | PostgreSQL type | Nullability | Default | Description / constraints role |
|---|---|---|---|---|
| `source_device_key_id` | `uuid` | NOT NULL | none | PK and FK-equal to authoritative binding key. |
| `tenant_id` | `uuid` | NOT NULL | none | Tenant consistency. |
| `asset_data_source_id` | `uuid` | NOT NULL | none | FK to `core.asset_data_source`; 1:1 unique. |
| `key_status` | `text` | NOT NULL | `'active'` | Mirror/derived status (must not conflict). |
| `created_at` | `timestamptz` | NOT NULL | `now()` proposed | Creation time. |

- **Foreign-key relationships:** FK (`asset_data_source_id`)→`core.asset_data_source`; tenant consistency required. If this table is not materialized, `source_device_key_id` remains an attribute/identity owned by `core.asset_data_source` only (preferred simplicity unless constraints require projection).
- **Unique constraints:** `uq_source_device_key_binding` on (`asset_data_source_id`).
- **Check constraints (proposed):** status alignment rules as applicable.

#### `core.source_device_fingerprint_alias`
- **Logical entity:** `source_device_fingerprint_alias`
- **Business purpose:** Versioned fingerprint/alias lookup record resolving to the same stable binding identity (non-permanent lookup, not competing identity).
- **Primary key:** `source_device_fingerprint_alias_id uuid`
- **Candidate alternate keys:** (`tenant_id`, `fingerprint_hash`/algorithm+value representation, active/effective scope) unique as policy requires; must prevent ambiguous active resolution.
- **Tenant ownership semantics:** Tenant-owned.
- **Lifecycle and deletion behavior:** Effective-dated/versioned; overlapping states possible during controlled rotation per policy; superseded aliases retained for audit/provenance.
- **Audit requirements:** Creation, activation, overlap, supersession, rotation, and conflict handling auditable.
- **Sensitive-data classification:** Sensitive device fingerprint material/derived identifiers; storage/protection requirements apply (OD-006 open).
- **Shared columns:** Standard shared columns.

| Column | PostgreSQL type | Nullability | Default | Description / constraints role |
|---|---|---|---|---|
| `source_device_fingerprint_alias_id` | `uuid` | NOT NULL | generated | PK. |
| `tenant_id` | `uuid` | NOT NULL | none | FK to `core.tenant`. |
| `asset_data_source_id` | `uuid` | NOT NULL | none | FK to authoritative binding. |
| `source_device_key_id` | `uuid` | NOT NULL | none | Stable binding identity reference (denormalized for lookup integrity; must match binding). |
| `fingerprint_algorithm` | `text` | NOT NULL | none | Algorithm/version identifier. |
| `fingerprint_value_protected` | `text` or `bytea` | NOT NULL | none | Protected/hashed/derived fingerprint representation per security design (no plaintext where avoidable). |
| `alias_status` | `text` | NOT NULL | `'active'` | CHECK constrained. |
| `effective_from` | `timestamptz` | NOT NULL | none | Validity start. |
| `effective_to` | `timestamptz` | NULL | null | Validity end/supersession. |
| `version_number` | `integer` | NOT NULL | 1 | Version sequence per binding/identity context. |

- **Foreign-key relationships:** FKs to `core.tenant` and `core.asset_data_source`; tenant/binding consistency required.
- **Unique constraints:** proposed uniqueness on active/effective fingerprint identity scope (exact partial unique predicate TBD with OD-006/overlap semantics).
- **Check constraints (proposed):** `version_number > 0`; effective window consistency; status validity.

#### `core.asset_identity_claim`
- **Logical entity:** `asset_identity_claim`
- **Business purpose:** Evidence/provenance claim or observation asserting identity attributes/binding candidates from a source.
- **Primary key:** `asset_identity_claim_id uuid`
- **Candidate alternate keys:** optional dedupe key per (`tenant_id`,`data_source_id`,`source_claim_reference`) if source provides stable IDs.
- **Tenant ownership semantics:** Tenant-owned.
- **Lifecycle and deletion behavior:** Append-oriented/retained for provenance; status may evolve (accepted/rejected/superseded).
- **Audit requirements:** Creation and resolution linkage auditable.
- **Sensitive-data classification:** May contain sensitive device/identity attributes (minimize and classify).
- **Shared columns:** Standard shared columns (append-oriented behavior preferred).

| Column | PostgreSQL type | Nullability | Default | Description / constraints role |
|---|---|---|---|---|
| `asset_identity_claim_id` | `uuid` | NOT NULL | generated | PK. |
| `tenant_id` | `uuid` | NOT NULL | none | FK to tenant. |
| `asset_id` | `uuid` | NULL | null | FK to `core.asset` when attributed/resolved. |
| `asset_data_source_id` | `uuid` | NULL | null | FK to binding when known. |
| `data_source_id` | `uuid` | NOT NULL | none | FK to source. |
| `identity_resolution_case_id` | `uuid` | NULL | null | FK to resolution case. |
| `claim_status` | `text` | NOT NULL | `'received'` | CHECK constrained. |
| `observed_at` | `timestamptz` | NOT NULL | none | Observation time. |
| `source_claim_reference` | `text` | NULL | null | Source-side reference. |
| `claim_payload` | `jsonb` | NULL | null | Limited structured claim attributes; purpose/validation/minimization required. |
| `confidence_level` | `text` | NULL | null | Confidence/provenance indicator. |

- **Foreign-key relationships:** FKs to tenant, asset, binding, data source, resolution case.
- **Unique constraints:** optional policy-dependent uniqueness on source claim reference.
- **Check constraints (proposed):** valid status.

#### `core.identity_resolution_case`
- **Logical entity:** `identity_resolution_case`
- **Business purpose:** Tracks ambiguous/conflicting/pending identity resolution requiring deterministic handling or manual review.
- **Primary key:** `identity_resolution_case_id uuid`
- **Candidate alternate keys:** optional case reference number unique per tenant.
- **Tenant ownership semantics:** Tenant-owned.
- **Lifecycle and deletion behavior:** Open/in-review/resolved/rejected/escalated states; retained.
- **Audit requirements:** State transitions, decisions, actors, and evidence links auditable.
- **Sensitive-data classification:** Sensitive operational/identity context.
- **Shared columns:** Standard shared columns.

| Column | PostgreSQL type | Nullability | Default | Description / constraints role |
|---|---|---|---|---|
| `identity_resolution_case_id` | `uuid` | NOT NULL | generated | PK. |
| `tenant_id` | `uuid` | NOT NULL | none | FK to tenant. |
| `case_status` | `text` | NOT NULL | `'open'` | CHECK constrained. |
| `case_type` | `text` | NOT NULL | none | Conflict/ambiguity/re-enrollment etc. |
| `primary_asset_id` | `uuid` | NULL | null | Candidate/affected asset. |
| `candidate_asset_data_source_id` | `uuid` | NULL | null | Related binding. |
| `opened_at` | `timestamptz` | NOT NULL | `now()` proposed | Open time. |
| `resolved_at` | `timestamptz` | NULL | null | Resolution time. |
| `resolution_outcome` | `text` | NULL | null | Outcome summary/code. |
| `resolution_notes` | `text` | NULL | null | Controlled notes (sensitivity-aware). |

- **Foreign-key relationships:** FKs to tenant, asset, binding; referenced by claims and possibly merge/split operations.
- **Unique constraints:** none mandatory.
- **Check constraints (proposed):** valid status; resolution timestamp consistency.

#### `core.asset_lifecycle_event`
- **Logical entity:** `asset_lifecycle_event`
- **Business purpose:** Append-oriented history of asset lifecycle transitions and significant state changes.
- **Primary key:** `asset_lifecycle_event_id uuid`
- **Candidate alternate keys:** none; optional idempotency/correlation uniqueness per event source if needed.
- **Tenant ownership semantics:** Tenant-owned.
- **Lifecycle and deletion behavior:** Append-only/immutable intent; no in-place destructive mutation; retention governed by policy.
- **Audit requirements:** Itself an auditable history record; correlated with `audit_evidence.audit_event`.
- **Sensitive-data classification:** Operational history.
- **Shared columns:** `created_at`/`recorded_at` immutable; `updated_at` typically not used (append-only).

| Column | PostgreSQL type | Nullability | Default | Description / constraints role |
|---|---|---|---|---|
| `asset_lifecycle_event_id` | `uuid` | NOT NULL | generated | PK. |
| `tenant_id` | `uuid` | NOT NULL | none | FK to tenant. |
| `asset_id` | `uuid` | NOT NULL | none | FK to asset. |
| `event_type` | `text` | NOT NULL | none | Transition/action type. |
| `from_status` | `text` | NULL | null | Prior state. |
| `to_status` | `text` | NULL | null | New state. |
| `occurred_at` | `timestamptz` | NOT NULL | none | Effective/observed transition time. |
| `actor_subject_id` | `uuid` | NULL | null | Acting principal if applicable. |
| `reason` | `text` | NULL | null | Reason/justification. |
| `correlation_id` | `text` | NULL | null | Trace correlation. |
| `details` | `jsonb` | NULL | null | Limited structured non-authoritative details. |

- **Foreign-key relationships:** FKs to tenant, asset, optional actor.
- **Unique constraints:** none mandatory.
- **Check constraints (proposed):** valid event type conventions where constrained.

#### `core.asset_merge_operation`
- **Logical entity:** `asset_merge_operation`
- **Business purpose:** Authorized, auditable merge operation record preserving lineage and controlling licensing impact.
- **Primary key:** `asset_merge_operation_id uuid`
- **Candidate alternate keys:** optional operation reference unique per tenant.
- **Tenant ownership semantics:** Tenant-owned.
- **Lifecycle and deletion behavior:** Immutable operation record (state transitions allowed if modeled) retained for history.
- **Audit requirements:** Mandatory authorization, rationale, actors, evidence, before/after state references.
- **Sensitive-data classification:** Sensitive operational/audit metadata.
- **Shared columns:** Standard shared columns.

| Column | PostgreSQL type | Nullability | Default | Description / constraints role |
|---|---|---|---|---|
| `asset_merge_operation_id` | `uuid` | NOT NULL | generated | PK. |
| `tenant_id` | `uuid` | NOT NULL | none | FK to tenant. |
| `operation_status` | `text` | NOT NULL | `'pending'` | CHECK constrained. |
| `surviving_asset_id` | `uuid` | NOT NULL | none | FK to canonical surviving asset. |
| `losing_asset_id` | `uuid` | NOT NULL | none | FK to merged-away asset (must become terminal/non-reusable). |
| `authorized_by_subject_id` | `uuid` | NULL | null | Authorizing principal. |
| `reason` | `text` | NOT NULL | none | Justification. |
| `evidence_reference` | `text` | NULL | null | Link/reference to supporting evidence/case. |
| `requested_at` | `timestamptz` | NOT NULL | none | Request/initiation time. |
| `completed_at` | `timestamptz` | NULL | null | Completion time. |
| `idempotency_key` | `text` | NULL | null | Optional operation idempotency correlation (ledger remains source of truth for identity/licensing ops). |

- **Foreign-key relationships:** FKs to tenant and assets; referenced by `core.asset_lineage_link` (merge link type).
- **Unique constraints:** none mandatory beyond PK; optional operation reference.
- **Check constraints (proposed):** `surviving_asset_id <> losing_asset_id`.

#### `core.asset_split_operation`
- **Logical entity:** `asset_split_operation`
- **Business purpose:** Authorized, auditable split operation record with typed lineage and licensing controls.
- **Primary key:** `asset_split_operation_id uuid`
- **Candidate alternate keys:** optional operation reference unique per tenant.
- **Tenant ownership semantics:** Tenant-owned.
- **Lifecycle and deletion behavior:** Immutable/retained operation record.
- **Audit requirements:** Mandatory authorization, rationale, evidence, resulting asset set accountability.
- **Sensitive-data classification:** Sensitive operational/audit metadata.
- **Shared columns:** Standard shared columns.

| Column | PostgreSQL type | Nullability | Default | Description / constraints role |
|---|---|---|---|---|
| `asset_split_operation_id` | `uuid` | NOT NULL | generated | PK. |
| `tenant_id` | `uuid` | NOT NULL | none | FK to tenant. |
| `operation_status` | `text` | NOT NULL | `'pending'` | CHECK constrained. |
| `source_asset_id` | `uuid` | NOT NULL | none | FK to source asset. |
| `authorized_by_subject_id` | `uuid` | NULL | null | Authorizing principal. |
| `reason` | `text` | NOT NULL | none | Justification. |
| `evidence_reference` | `text` | NULL | null | Supporting evidence/case reference. |
| `requested_at` | `timestamptz` | NOT NULL | none | Request/initiation time. |
| `completed_at` | `timestamptz` | NULL | null | Completion time. |

- **Foreign-key relationships:** FKs to tenant and source asset; referenced by lineage links (split link type).
- **Unique constraints:** none mandatory.
- **Check constraints (proposed):** valid status.

#### `core.asset_lineage_link`
- **Logical entity:** `asset_lineage_link`
- **Business purpose:** Typed relational lineage between assets and merge/split operations (replaces polymorphic reference).
- **Primary key:** `asset_lineage_link_id uuid`
- **Candidate alternate keys:** uniqueness per (`tenant_id`,`from_asset_id`,`to_asset_id`,`link_type`,`operation context`) as needed to prevent duplicates.
- **Tenant ownership semantics:** Tenant-owned.
- **Lifecycle and deletion behavior:** Append-only/immutable history record.
- **Audit requirements:** Correlated with operation and lifecycle audit records.
- **Sensitive-data classification:** Operational history.
- **Shared columns:** `created_at`/immutable record timestamp; `updated_at` typically not used.

| Column | PostgreSQL type | Nullability | Default | Description / constraints role |
|---|---|---|---|---|
| `asset_lineage_link_id` | `uuid` | NOT NULL | generated | PK. |
| `tenant_id` | `uuid` | NOT NULL | none | FK to tenant. |
| `link_type` | `text` | NOT NULL | none | e.g. `merge`, `split` (CHECK constrained). |
| `from_asset_id` | `uuid` | NOT NULL | none | Typed FK to source/losing/from asset. |
| `to_asset_id` | `uuid` | NOT NULL | none | Typed FK to target/surviving/result asset. |
| `merge_operation_id` | `uuid` | NULL | null | Typed FK to `core.asset_merge_operation` when `link_type='merge'`. |
| `split_operation_id` | `uuid` | NULL | null | Typed FK to `core.asset_split_operation` when `link_type='split'`. |
| `effective_at` | `timestamptz` | NOT NULL | none | Effective lineage time. |
| `notes` | `text` | NULL | null | Optional controlled note. |

- **Foreign-key relationships:** FKs to tenant, both assets, merge op, split op.
- **Unique constraints:** proposed uniqueness to prevent duplicate lineage edges per operation context.
- **Check constraints (proposed):** mutual exclusivity `((link_type='merge' AND merge_operation_id IS NOT NULL AND split_operation_id IS NULL) OR (link_type='split' AND split_operation_id IS NOT NULL AND merge_operation_id IS NULL))`; `from_asset_id <> to_asset_id` where semantically required.

#### `core.subscription_entitlement`
- **Logical entity:** `subscription_entitlement`
- **Business purpose:** Tenant licensing/subscription entitlement terms and capacity basis (commercial semantics Proposed/open).
- **Primary key:** `subscription_entitlement_id uuid`
- **Candidate alternate keys:** (`tenant_id`, `entitlement_code`, `effective_from`) or external subscription reference unique per tenant.
- **Tenant ownership semantics:** Tenant-owned.
- **Lifecycle and deletion behavior:** Effective-dated/versioned; historical entitlements retained.
- **Audit requirements:** Creation/change/suspension auditable.
- **Sensitive-data classification:** Commercial/contract-sensitive.
- **Shared columns:** Standard shared columns.

| Column | PostgreSQL type | Nullability | Default | Description / constraints role |
|---|---|---|---|---|
| `subscription_entitlement_id` | `uuid` | NOT NULL | generated | PK. |
| `tenant_id` | `uuid` | NOT NULL | none | FK to tenant. |
| `entitlement_code` | `text` | NOT NULL | none | Plan/entitlement identifier. |
| `entitlement_status` | `text` | NOT NULL | `'active'` | CHECK constrained. |
| `licensed_asset_limit` | `integer` | NULL | null | Authorized unique-device capacity (semantics open; OD-001/003). |
| `effective_from` | `timestamptz` | NOT NULL | none | Start. |
| `effective_to` | `timestamptz` | NULL | null | End. |
| `external_subscription_ref` | `text` | NULL | null | External billing/subscription reference. |
| `terms` | `jsonb` | NULL | null | Structured non-authoritative/commercial terms snapshot as needed. |

- **Foreign-key relationships:** FK to tenant; referenced by usage/accounting records.
- **Unique constraints:** proposed uniqueness per tenant/code/effective window or external ref.
- **Check constraints (proposed):** non-negative limit when present; window consistency.

#### `core.tenant_license_usage_state`
- **Logical entity:** `tenant_license_usage_state`
- **Business purpose:** Tenant-scoped authoritative/materialized licensing usage/capacity state for atomic enforcement (counter semantics Proposed/open).
- **Primary key:** `tenant_license_usage_state_id uuid` or (`tenant_id`, `usage_scope`) composite PK (proposed surrogate for consistency).
- **Candidate alternate keys:** (`tenant_id`, `usage_scope`) unique.
- **Tenant ownership semantics:** Tenant-owned.
- **Lifecycle and deletion behavior:** Updated transactionally; reset/recompute only via controlled reconciliation with audit.
- **Audit requirements:** All material changes and reconciliation auditable (events/ledger).
- **Sensitive-data classification:** Commercial/operational-sensitive.
- **Shared columns:** Standard shared columns including `row_version` (optimistic/concurrency marker recommended).

| Column | PostgreSQL type | Nullability | Default | Description / constraints role |
|---|---|---|---|---|
| `tenant_license_usage_state_id` | `uuid` | NOT NULL | generated | PK. |
| `tenant_id` | `uuid` | NOT NULL | none | FK to tenant. |
| `usage_scope` | `text` | NOT NULL | `'default'` | Scope key (future-proofing). |
| `subscription_entitlement_id` | `uuid` | NULL | null | FK to active entitlement context. |
| `committed_asset_count` | `integer` | NOT NULL | 0 | Committed unique licensed assets (semantics OD-003/004). |
| `reserved_asset_count` | `integer` | NOT NULL | 0 | Reserved count if reservation model adopted (OD-003). |
| `available_count_derived` | `integer` | NULL | null | Optional derived/persisted convenience value; authoritative derivation rules must be explicit if stored. |
| `last_reconciled_at` | `timestamptz` | NULL | null | Reconciliation marker. |

- **Foreign-key relationships:** FKs to tenant and entitlement.
- **Unique constraints:** `uq_tenant_license_usage_scope` on (`tenant_id`, `usage_scope`).
- **Check constraints (proposed):** non-negative counts; invariant relationships as approved (e.g. within entitlement limits) — exact formulas dependent on OD-001/003/004.

#### `core.asset_license_event`
- **Logical entity:** `asset_license_event`
- **Business purpose:** Append-oriented history of licensing allocation/release/reservation/adjustment events.
- **Primary key:** `asset_license_event_id uuid`
- **Candidate alternate keys:** optional correlation/idempotency reference.
- **Tenant ownership semantics:** Tenant-owned.
- **Lifecycle and deletion behavior:** Append-only, retained per policy.
- **Audit requirements:** Core licensing audit trail.
- **Sensitive-data classification:** Commercial/operational-sensitive.
- **Shared columns:** Immutable `created_at`/`occurred_at`; no routine updates.

| Column | PostgreSQL type | Nullability | Default | Description / constraints role |
|---|---|---|---|---|
| `asset_license_event_id` | `uuid` | NOT NULL | generated | PK. |
| `tenant_id` | `uuid` | NOT NULL | none | FK to tenant. |
| `asset_id` | `uuid` | NULL | null | FK to asset when applicable. |
| `event_type` | `text` | NOT NULL | none | Allocation/reservation/release/merge/split/adjustment. |
| `delta_committed` | `integer` | NOT NULL | 0 | Change applied (semantics proposed). |
| `delta_reserved` | `integer` | NOT NULL | 0 | Reservation delta if applicable. |
| `occurred_at` | `timestamptz` | NOT NULL | none | Event time. |
| `operation_reference_type` | `text` | NULL | null | Correlation type (ledger/merge/split/etc.). |
| `operation_reference_id` | `uuid` | NULL | null | Correlation ID. |
| `reason` | `text` | NULL | null | Explanation. |

- **Foreign-key relationships:** FKs to tenant, asset.
- **Unique constraints:** none mandatory.
- **Check constraints (proposed):** valid event type.

#### `core.identity_operation_idempotency_ledger`
- **Logical entity:** `identity_operation_idempotency_ledger`
- **Business purpose:** Durable idempotency contract for identity/licensing operations (Round 1.1, OD-008 Proposed/open); prevents duplicate licensed usage/effects under retries/concurrency/recovery.
- **Primary key:** `identity_operation_idempotency_ledger_id uuid`
- **Candidate alternate keys:** **(`tenant_id`, `operation_type`, `idempotency_key`) unique** (required scope).
- **Tenant ownership semantics:** Tenant-owned.
- **Lifecycle and deletion behavior:** State transitions per contract; retention/archival subject to reconciliation and policy (not immediate deletion).
- **Audit requirements:** Required for correctness/auditability; linked to audit/license/lifecycle records.
- **Sensitive-data classification:** Operationally sensitive; request hash/summary must avoid sensitive payload leakage.
- **Shared columns:** `created_at`, `updated_at`, `row_version` recommended.

| Column | PostgreSQL type | Nullability | Default | Description / constraints role |
|---|---|---|---|---|
| `identity_operation_idempotency_ledger_id` | `uuid` | NOT NULL | generated | PK. |
| `tenant_id` | `uuid` | NOT NULL | none | FK to tenant; scope component. |
| `operation_type` | `text` | NOT NULL | none | Operation class; scope component. |
| `idempotency_key` | `text` | NOT NULL | none | Caller/client operation key; scope component. |
| `canonical_request_hash` | `text` | NOT NULL | none | Deterministic hash of canonicalized semantic request. |
| `request_state` | `text` | NOT NULL | `'in_progress'` | `in_progress`/`committed`/`failed_terminal`/`timeout_unknown_commit` (CHECK). |
| `outcome_code` | `text` | NULL | null | Result classification. |
| `outcome_reference_type` | `text` | NULL | null | Asset/operation reference type. |
| `outcome_reference_id` | `uuid` | NULL | null | Resulting canonical asset/operation ID when known. |
| `started_at` | `timestamptz` | NOT NULL | `now()` proposed | First attempt start. |
| `completed_at` | `timestamptz` | NULL | null | Terminal completion time. |
| `last_attempt_at` | `timestamptz` | NOT NULL | `now()` proposed | Most recent attempt. |
| `conflict_detected_at` | `timestamptz` | NULL | null | Payload-conflict detection time. |
| `reconciliation_status` | `text` | NULL | null | Unknown-commit reconciliation state. |
| `request_summary` | `jsonb` | NULL | null | Minimal non-sensitive canonical summary if needed (careful minimization). |

- **Foreign-key relationships:** FK to tenant; logical references to operation outcomes.
- **Unique constraints:** **`uq_identity_idempotency_scope` on (`tenant_id`, `operation_type`, `idempotency_key`)**.
- **Check constraints (proposed):** valid request states; hash/key non-empty; state/timestamp consistency.

#### `core.asset_license_reservation`
- **Logical entity:** `asset_license_reservation`
- **Business purpose:** Optional/policy-dependent reservation of licensed capacity for in-progress onboarding/allocation (OD-003 Proposed/open).
- **Primary key:** `asset_license_reservation_id uuid`
- **Candidate alternate keys:** (`tenant_id`, `reservation_key`) or linkage to ledger/operation unique.
- **Tenant ownership semantics:** Tenant-owned.
- **Lifecycle and deletion behavior:** Active/consumed/released/expired states; retained for reconciliation/audit.
- **Audit requirements:** Creation, consumption, release, expiry auditable.
- **Sensitive-data classification:** Commercial/operational-sensitive.
- **Shared columns:** Standard shared columns.

| Column | PostgreSQL type | Nullability | Default | Description / constraints role |
|---|---|---|---|---|
| `asset_license_reservation_id` | `uuid` | NOT NULL | generated | PK. |
| `tenant_id` | `uuid` | NOT NULL | none | FK to tenant. |
| `subscription_entitlement_id` | `uuid` | NULL | null | FK to entitlement context. |
| `asset_id` | `uuid` | NULL | null | FK to asset if reserved for specific canonical asset. |
| `ledger_id` | `uuid` | NULL | null | FK to idempotency ledger when applicable. |
| `reservation_status` | `text` | NOT NULL | `'active'` | CHECK constrained. |
| `reserved_units` | `integer` | NOT NULL | 1 | Units reserved (device-level licensing implies 1 in typical case). |
| `expires_at` | `timestamptz` | NULL | null | Expiry/timeout boundary. |
| `released_at` | `timestamptz` | NULL | null | Release/consume time. |

- **Foreign-key relationships:** FKs to tenant, entitlement, asset, ledger.
- **Unique constraints:** proposed uniqueness per reservation key/operation linkage.
- **Check constraints (proposed):** `reserved_units > 0`; valid status.

#### `core.asset_tombstone`
- **Logical entity:** `asset_tombstone`
- **Business purpose:** Distinct optional terminal historical record for deactivated/removed/merged-away/split-replaced assets, preserving identity continuity without reuse.
- **Primary key:** `asset_tombstone_id uuid` (or 1:1 with `asset_id` depending on model)
- **Candidate alternate keys:** (`tenant_id`, `asset_id`) unique (one tombstone per terminal asset).
- **Tenant ownership semantics:** Tenant-owned.
- **Lifecycle and deletion behavior:** Created when asset reaches terminal represented state; immutable thereafter except controlled administrative annotations if explicitly allowed.
- **Audit requirements:** Creation reason/actor/operation linkage auditable.
- **Sensitive-data classification:** Operational history.
- **Shared columns:** Immutable creation metadata; no routine `updated_at` mutation.

| Column | PostgreSQL type | Nullability | Default | Description / constraints role |
|---|---|---|---|---|
| `asset_tombstone_id` | `uuid` | NOT NULL | generated | PK. |
| `tenant_id` | `uuid` | NOT NULL | none | FK to tenant. |
| `asset_id` | `uuid` | NOT NULL | none | FK to `core.asset`; unique terminal representation. |
| `terminal_state` | `text` | NOT NULL | none | Terminal classification. |
| `terminal_reason` | `text` | NOT NULL | none | Reason. |
| `superseded_by_asset_id` | `uuid` | NULL | null | Surviving/result asset reference when applicable. |
| `operation_type` | `text` | NULL | null | merge/split/deactivation/removal. |
| `operation_id` | `uuid` | NULL | null | Related operation record. |
| `tombstoned_at` | `timestamptz` | NOT NULL | none | Effective time. |

- **Foreign-key relationships:** FKs to tenant and assets.
- **Unique constraints:** `uq_asset_tombstone_asset` on (`tenant_id`, `asset_id`).
- **Check constraints (proposed):** valid terminal state.

### 6.3 Ingest and event domain

#### `ingest.event_schema_reference`
- **Logical entity:** `event_schema_reference`
- **Business purpose:** Schema/version/normalization contract reference for ingested events.
- **Primary key:** `event_schema_reference_id uuid`
- **Candidate alternate keys:** (`schema_namespace`, `schema_name`, `schema_version`) unique.
- **Tenant ownership semantics:** Proposed global/shared catalog (optionally tenant-extensible later; default global to avoid duplication).
- **Lifecycle and deletion behavior:** Immutable/versioned references; deprecated rather than deleted when historically referenced.
- **Audit requirements:** Registration/deprecation changes auditable.
- **Sensitive-data classification:** Non-sensitive metadata.
- **Shared columns:** `created_at`, `updated_at`, actor columns.

| Column | PostgreSQL type | Nullability | Default | Description / constraints role |
|---|---|---|---|---|
| `event_schema_reference_id` | `uuid` | NOT NULL | generated | PK. |
| `schema_namespace` | `text` | NOT NULL | none | Namespace/provider/domain. |
| `schema_name` | `text` | NOT NULL | none | Schema identifier. |
| `schema_version` | `text` | NOT NULL | none | Version string/identifier. |
| `compatibility_status` | `text` | NOT NULL | `'active'` | Active/deprecated/retired. |
| `validation_contract_ref` | `text` | NULL | null | Reference to validation/normalization contract artifact. |
| `description` | `text` | NULL | null | Purpose/notes. |

- **Foreign-key relationships:** Referenced by `ingest.event_receipt` and/or `ingest.security_event`.
- **Unique constraints:** `uq_event_schema_ref` on (`schema_namespace`, `schema_name`, `schema_version`).
- **Check constraints (proposed):** non-empty identifiers.

#### `ingest.event_receipt`
- **Logical entity:** `event_receipt`
- **Business purpose:** Durable ingestion idempotency/acceptance record with explicit deduplication namespace distinct from identity/licensing ledger (Round 1.1, OD-013).
- **Primary key:** `event_receipt_id uuid`
- **Candidate alternate keys:** **explicit dedup namespace uniqueness** (proposed physical form): `uq_event_receipt_dedup` on (`tenant_id`, `data_source_id`, `source_device_key_id`, `upstream_event_identifier`, `event_namespace`) where `upstream_event_identifier` is present and source-scoped; alternative data-source-global form must be explicitly represented when approved.
- **Tenant ownership semantics:** Tenant-owned.
- **Lifecycle and deletion behavior:** Append/acceptance record with processing-state updates; retention/archival per lifecycle policy (partition candidate).
- **Audit requirements:** Acceptance, duplicate detection, rejection/validation outcomes auditable/correlatable.
- **Sensitive-data classification:** May contain sensitive metadata/payload references; payload minimization required.
- **Shared columns:** `created_at`, `updated_at`, actor/system columns, `row_version` where claim/state updates occur.

| Column | PostgreSQL type | Nullability | Default | Description / constraints role |
|---|---|---|---|---|
| `event_receipt_id` | `uuid` | NOT NULL | generated | PK. |
| `tenant_id` | `uuid` | NOT NULL | none | FK to tenant. |
| `data_source_id` | `uuid` | NOT NULL | none | FK to data source (namespace/provenance). |
| `asset_data_source_id` | `uuid` | NULL | null | FK to authoritative binding when resolved. |
| `source_device_key_id` | `uuid` | NULL | null | Stable binding identity for device-scoped dedup namespace (required when upstream ID is device-scoped in multi-device connectors). |
| `asset_id` | `uuid` | NULL | null | FK to canonical asset when attributed. |
| `event_namespace` | `text` | NOT NULL | none | Explicit dedup namespace classification (e.g. device-scoped/data-source-global/connector-defined). |
| `upstream_event_identifier` | `text` | NULL | null | Upstream event ID if provided/reliable. |
| `fallback_dedup_fingerprint` | `text` | NULL | null | Deterministic fallback fingerprint when upstream ID missing/unreliable (connector-specific policy, OD-013). |
| `receipt_status` | `text` | NOT NULL | `'accepted'` | accepted/duplicate/rejected/processing states (CHECK). |
| `received_at` | `timestamptz` | NOT NULL | none | Ingestion receive time. |
| `event_time` | `timestamptz` | NULL | null | Source/event occurrence time. |
| `event_schema_reference_id` | `uuid` | NULL | null | FK to schema reference. |
| `idempotency_basis` | `text` | NOT NULL | none | `upstream_id`/`fingerprint`/`other` (explicit). |
| `payload_hash` | `text` | NULL | null | Integrity/dedup support hash. |
| `raw_payload_ref` | `text` | NULL | null | External/object-store or internal payload reference (not large inline blob by default). |
| `normalized_payload` | `jsonb` | NULL | null | Limited normalized subset only when justified; avoid duplicating full raw payloads. |
| `duplicate_of_receipt_id` | `uuid` | NULL | null | Self-reference to canonical accepted receipt when duplicate detected. |

- **Foreign-key relationships:** FKs to tenant, data source, binding, asset, schema reference, self.
- **Unique constraints:** proposed conditional unique indexes enforcing explicit namespace semantics (e.g. device-scoped key includes `source_device_key_id`; fallback fingerprint uniqueness scoped appropriately). Exact predicates depend on OD-013/connector semantics.
- **Check constraints (proposed):** at least one dedup basis (`upstream_event_identifier` or `fallback_dedup_fingerprint`) present; device-scoped namespace requires `source_device_key_id` when policy mandates; valid status.

#### `ingest.security_event`
- **Logical entity:** `security_event`
- **Business purpose:** Normalized/queryable accepted security or operational event with correlation to assets/sources/receipts.
- **Primary key:** `security_event_id uuid`
- **Candidate alternate keys:** (`tenant_id`, `event_receipt_id`) unique when 1:1 with receipt; otherwise event reference unique per tenant.
- **Tenant ownership semantics:** Tenant-owned.
- **Lifecycle and deletion behavior:** Immutable or append-oriented analytical record; retention/partitioning governed by lifecycle policy.
- **Audit requirements:** Correlatable to ingest receipt and audit events.
- **Sensitive-data classification:** Potentially sensitive security telemetry; minimization/classification required.
- **Shared columns:** `created_at` immutable, optional `updated_at` limited.

| Column | PostgreSQL type | Nullability | Default | Description / constraints role |
|---|---|---|---|---|
| `security_event_id` | `uuid` | NOT NULL | generated | PK. |
| `tenant_id` | `uuid` | NOT NULL | none | FK to tenant. |
| `event_receipt_id` | `uuid` | NOT NULL | none | FK to `ingest.event_receipt`. |
| `asset_id` | `uuid` | NULL | null | FK to asset. |
| `data_source_id` | `uuid` | NOT NULL | none | FK to data source. |
| `event_schema_reference_id` | `uuid` | NULL | null | FK to schema reference. |
| `event_type` | `text` | NOT NULL | none | Normalized type/category. |
| `severity` | `text` | NULL | null | Normalized severity. |
| `event_time` | `timestamptz` | NOT NULL | none | Event occurrence time. |
| `ingested_at` | `timestamptz` | NOT NULL | none | Acceptance/normalization time. |
| `correlation_id` | `text` | NULL | null | Trace correlation. |
| `normalized_attributes` | `jsonb` | NULL | null | Bounded normalized attributes; justified JSONB use. |

- **Foreign-key relationships:** FKs to tenant, receipt, asset, data source, schema reference.
- **Unique constraints:** proposed `uq_security_event_receipt` on (`tenant_id`, `event_receipt_id`) if 1:1.
- **Check constraints (proposed):** valid severity/category values where constrained.

### 6.4 Processing and async coordination domain

#### `processing.outbox_message`
- **Logical entity:** `outbox_message`
- **Business purpose:** Durable async work intent/state created atomically with business-state changes in the same DB transaction where applicable.
- **Primary key:** `outbox_message_id uuid`
- **Candidate alternate keys:** (`tenant_id`, `dedupe_key`) unique when dedupe key used; optional business correlation key.
- **Tenant ownership semantics:** Tenant-owned or tenant-contextual (nullable tenant only for explicitly global control-plane messages, if any; default tenant-owned).
- **Lifecycle and deletion behavior:** Pending/available/claimed/in-flight/completed/dead-letter/cancelled states; retention/cleanup after terminal outcome per policy.
- **Audit requirements:** State transitions and delivery outcomes auditable via attempts and audit events.
- **Sensitive-data classification:** May reference sensitive operations; payload minimized and governed.
- **Shared columns:** Standard shared columns including `row_version`.

| Column | PostgreSQL type | Nullability | Default | Description / constraints role |
|---|---|---|---|---|
| `outbox_message_id` | `uuid` | NOT NULL | generated | PK. |
| `tenant_id` | `uuid` | NULL | null | FK to tenant when tenant-scoped (expected most cases). |
| `message_type` | `text` | NOT NULL | none | Work category. |
| `aggregate_type` | `text` | NULL | null | Source aggregate/entity type. |
| `aggregate_id` | `uuid` | NULL | null | Source aggregate/entity ID. |
| `message_status` | `text` | NOT NULL | `'pending'` | CHECK constrained. |
| `payload` | `jsonb` | NOT NULL | none | Minimal dispatch payload/reference; sensitive content excluded or protected. |
| `dedupe_key` | `text` | NULL | null | Optional idempotent enqueue key. |
| `available_at` | `timestamptz` | NOT NULL | `now()` proposed | When eligible for claim. |
| `last_attempt_at` | `timestamptz` | NULL | null | Last claim/attempt time. |
| `completed_at` | `timestamptz` | NULL | null | Terminal completion time. |
| `attempt_count` | `integer` | NOT NULL | 0 | Non-negative attempt counter. |

- **Foreign-key relationships:** FK to tenant (nullable as defined); referenced by `processing.outbox_attempt`.
- **Unique constraints:** proposed partial/conditional unique on (`tenant_id`, `dedupe_key`) where not null.
- **Check constraints (proposed):** `attempt_count >= 0`; valid status.

#### `processing.outbox_attempt`
- **Logical entity:** `outbox_attempt`
- **Business purpose:** Records claim/delivery attempts, lease/fencing/heartbeat metadata, outcomes, and unknown-delivery ambiguity for outbox processing.
- **Primary key:** `outbox_attempt_id uuid`
- **Candidate alternate keys:** optional (`outbox_message_id`, `attempt_number`) unique.
- **Tenant ownership semantics:** Inherits tenant context from message.
- **Lifecycle and deletion behavior:** Append-oriented attempt history; retained for recovery/audit; cleanup by policy.
- **Audit requirements:** Essential for at-least-once delivery reasoning and unknown-outcome handling.
- **Sensitive-data classification:** Operationally sensitive; avoid external sensitive payload copies.
- **Shared columns:** `created_at`, `updated_at` for status/heartbeat updates.

| Column | PostgreSQL type | Nullability | Default | Description / constraints role |
|---|---|---|---|---|
| `outbox_attempt_id` | `uuid` | NOT NULL | generated | PK. |
| `outbox_message_id` | `uuid` | NOT NULL | none | FK to `processing.outbox_message`. |
| `tenant_id` | `uuid` | NULL | null | Tenant consistency with message. |
| `attempt_number` | `integer` | NOT NULL | none | Monotonic per message. |
| `attempt_status` | `text` | NOT NULL | `'claimed'` | claimed/in_progress/succeeded/failed_retryable/failed_terminal/unknown (CHECK). |
| `claimed_by` | `text` | NULL | null | Worker/instance identifier. |
| `lease_token` | `text` | NULL | null | Fencing/lease token for stale-worker protection (Proposed). |
| `lease_expires_at` | `timestamptz` | NULL | null | Lease expiry. |
| `heartbeat_at` | `timestamptz` | NULL | null | Last heartbeat/progress signal. |
| `started_at` | `timestamptz` | NOT NULL | `now()` proposed | Attempt start. |
| `ended_at` | `timestamptz` | NULL | null | Attempt end. |
| `outcome_detail` | `text` | NULL | null | Bounded outcome/error classification. |
| `external_delivery_state` | `text` | NULL | null | Unknown/acknowledged/rejected as applicable (no exactly-once claim). |

- **Foreign-key relationships:** FK to `processing.outbox_message`, optional tenant.
- **Unique constraints:** proposed `uq_outbox_attempt_number` on (`outbox_message_id`, `attempt_number`).
- **Check constraints (proposed):** `attempt_number > 0`; valid status.

#### `processing.processing_work_item` (optional/non-core)
- **Logical entity:** `processing_work_item`
- **Business purpose:** Optional internal processing coordination record distinct from `event_receipt` acceptance truth and `outbox_message` delivery intent (Round 1.1 normalization).
- **Primary key:** `processing_work_item_id uuid`
- **Candidate alternate keys:** correlation/receipt/message linkage unique as needed.
- **Tenant ownership semantics:** Tenant-owned when applicable.
- **Lifecycle and deletion behavior:** Short-to-medium lived coordination states; cleanup per policy; must not replace receipt/outbox records.
- **Audit requirements:** State transitions auditable where used.
- **Sensitive-data classification:** Operational metadata.
- **Shared columns:** Standard shared columns.

| Column | PostgreSQL type | Nullability | Default | Description / constraints role |
|---|---|---|---|---|
| `processing_work_item_id` | `uuid` | NOT NULL | generated | PK. |
| `tenant_id` | `uuid` | NULL | null | FK to tenant when scoped. |
| `work_type` | `text` | NOT NULL | none | Processing category. |
| `work_status` | `text` | NOT NULL | `'pending'` | CHECK constrained. |
| `event_receipt_id` | `uuid` | NULL | null | FK to receipt when derived from ingestion. |
| `outbox_message_id` | `uuid` | NULL | null | FK to outbox message when applicable. |
| `available_at` | `timestamptz` | NOT NULL | `now()` proposed | Eligibility time. |
| `claimed_by` | `text` | NULL | null | Worker identifier. |
| `lease_expires_at` | `timestamptz` | NULL | null | Lease/claim expiry. |
| `correlation_id` | `text` | NULL | null | Trace correlation. |
| `payload` | `jsonb` | NULL | null | Minimal coordination payload. |

- **Foreign-key relationships:** FKs to tenant, receipt, outbox message.
- **Unique constraints:** policy-dependent (e.g. one active work item per receipt/type).
- **Check constraints (proposed):** valid status.

### 6.5 Audit and evidence domain

#### `audit_evidence.audit_event`
- **Logical entity:** `audit_event`
- **Business purpose:** Operational/security/audit metadata record for significant actions and state transitions (distinct from specialized AI interaction audit).
- **Primary key:** `audit_event_id uuid`
- **Candidate alternate keys:** optional external/event-stream correlation key.
- **Tenant ownership semantics:** Tenant-owned when action is tenant-scoped; nullable/global only for explicitly platform-level audited actions (must be tightly controlled).
- **Lifecycle and deletion behavior:** Append-only/immutable intent; retention and legal-hold controls apply.
- **Audit requirements:** Core audit log store (integrity protections required by security design).
- **Sensitive-data classification:** Security/audit-sensitive; must not contain secrets or unnecessary PII.
- **Shared columns:** `created_at`/`recorded_at` immutable.

| Column | PostgreSQL type | Nullability | Default | Description / constraints role |
|---|---|---|---|---|
| `audit_event_id` | `uuid` | NOT NULL | generated | PK. |
| `tenant_id` | `uuid` | NULL | null | Tenant scope when applicable. |
| `actor_subject_id` | `uuid` | NULL | null | Acting principal. |
| `actor_type` | `text` | NULL | null | human/service/support/system. |
| `action_type` | `text` | NOT NULL | none | Audited action/event type. |
| `target_entity_type` | `text` | NULL | null | Affected entity type. |
| `target_entity_id` | `uuid` | NULL | null | Affected entity ID. |
| `outcome` | `text` | NOT NULL | none | success/failure/denied/unknown. |
| `occurred_at` | `timestamptz` | NOT NULL | none | Event time. |
| `correlation_id` | `text` | NULL | null | Request/operation correlation. |
| `details` | `jsonb` | NULL | null | Bounded non-secret metadata. |

- **Foreign-key relationships:** Optional FKs to tenant and actor subject; logical correlation to other entities.
- **Unique constraints:** none mandatory.
- **Check constraints (proposed):** valid outcome.

#### `audit_evidence.forensic_evidence_record`
- **Logical entity:** `forensic_evidence_record`
- **Business purpose:** Authoritative metadata/provenance/state for preserved forensic evidence artifacts.
- **Primary key:** `forensic_evidence_record_id uuid`
- **Candidate alternate keys:** (`tenant_id`, `evidence_reference_code`) unique if assigned.
- **Tenant ownership semantics:** Tenant-owned (strict scope).
- **Lifecycle and deletion behavior:** Controlled state transitions only (e.g. collected/preserved/verified/released/legal-hold); original evidence never silently rewritten or deleted; legal hold blocks unauthorized disposal.
- **Audit requirements:** All transitions, access, custody, and verification events auditable.
- **Sensitive-data classification:** Highly sensitive forensic/legal evidence metadata.
- **Shared columns:** Standard shared columns with strict immutability expectations for integrity-critical fields.

| Column | PostgreSQL type | Nullability | Default | Description / constraints role |
|---|---|---|---|---|
| `forensic_evidence_record_id` | `uuid` | NOT NULL | generated | PK. |
| `tenant_id` | `uuid` | NOT NULL | none | FK to tenant. |
| `asset_id` | `uuid` | NULL | null | Related asset. |
| `evidence_status` | `text` | NOT NULL | `'collected'` | CHECK constrained. |
| `evidence_type` | `text` | NOT NULL | none | Classification. |
| `collected_at` | `timestamptz` | NOT NULL | none | Collection time. |
| `collected_by_subject_id` | `uuid` | NULL | null | Collector. |
| `source_reference` | `text` | NULL | null | Source/context reference. |
| `integrity_hash` | `text` | NULL | null | Current verified hash representation (per version/model). |
| `hash_algorithm` | `text` | NULL | null | Algorithm identifier. |
| `legal_hold` | `boolean` | NOT NULL | false | Prevents unauthorized disposal. |
| `retention_policy_ref` | `text` | NULL | null | Applicable retention/legal policy reference. |

- **Foreign-key relationships:** FKs to tenant, asset, actor; referenced by object versions, custody events, transition authorizations.
- **Unique constraints:** optional evidence reference code uniqueness.
- **Check constraints (proposed):** valid status.

#### `audit_evidence.evidence_object_version`
- **Logical entity:** `evidence_object_version`
- **Business purpose:** Immutable version/reference metadata for stored evidence objects (content stored in approved external/object storage as designed).
- **Primary key:** `evidence_object_version_id uuid`
- **Candidate alternate keys:** (`forensic_evidence_record_id`, `version_number`) unique.
- **Tenant ownership semantics:** Tenant-owned via evidence record.
- **Lifecycle and deletion behavior:** Immutable once recorded; deletion/retention governed by legal hold/policy and controlled procedures.
- **Audit requirements:** Creation and verification auditable.
- **Sensitive-data classification:** Highly sensitive (object location/hash metadata).
- **Shared columns:** Immutable `created_at`.

| Column | PostgreSQL type | Nullability | Default | Description / constraints role |
|---|---|---|---|---|
| `evidence_object_version_id` | `uuid` | NOT NULL | generated | PK. |
| `tenant_id` | `uuid` | NOT NULL | none | Tenant consistency. |
| `forensic_evidence_record_id` | `uuid` | NOT NULL | none | FK to evidence record. |
| `version_number` | `integer` | NOT NULL | none | Monotonic version. |
| `storage_uri` | `text` | NOT NULL | none | Approved storage location/reference (not public). |
| `content_hash` | `text` | NOT NULL | none | Integrity hash. |
| `hash_algorithm` | `text` | NOT NULL | none | Algorithm. |
| `content_size_bytes` | `bigint` | NULL | null | Size metadata. |
| `created_at` | `timestamptz` | NOT NULL | `now()` proposed | Immutable record time. |
| `created_by_subject_id` | `uuid` | NULL | null | Actor. |

- **Foreign-key relationships:** FK to tenant and evidence record.
- **Unique constraints:** `uq_evidence_object_version` on (`forensic_evidence_record_id`, `version_number`).
- **Check constraints (proposed):** `version_number > 0`, `content_size_bytes >= 0` when present.

#### `audit_evidence.evidence_custody_event`
- **Logical entity:** `evidence_custody_event`
- **Business purpose:** Append-only chain-of-custody event history for evidence records/versions.
- **Primary key:** `evidence_custody_event_id uuid`
- **Candidate alternate keys:** none mandatory.
- **Tenant ownership semantics:** Tenant-owned.
- **Lifecycle and deletion behavior:** Append-only/immutable.
- **Audit requirements:** Mandatory custody traceability.
- **Sensitive-data classification:** Highly sensitive forensic metadata.
- **Shared columns:** Immutable `recorded_at`/`created_at`.

| Column | PostgreSQL type | Nullability | Default | Description / constraints role |
|---|---|---|---|---|
| `evidence_custody_event_id` | `uuid` | NOT NULL | generated | PK. |
| `tenant_id` | `uuid` | NOT NULL | none | Tenant consistency. |
| `forensic_evidence_record_id` | `uuid` | NOT NULL | none | FK to evidence record. |
| `evidence_object_version_id` | `uuid` | NULL | null | FK to version if applicable. |
| `custody_action` | `text` | NOT NULL | none | Action type (collected/accessed/transferred/verified/released etc.). |
| `actor_subject_id` | `uuid` | NULL | null | Actor. |
| `occurred_at` | `timestamptz` | NOT NULL | none | Event time. |
| `reason` | `text` | NULL | null | Justification. |
| `details` | `jsonb` | NULL | null | Bounded metadata. |

- **Foreign-key relationships:** FKs to tenant, evidence record, version, actor.
- **Unique constraints:** none mandatory.
- **Check constraints (proposed):** valid action types where constrained.

#### `audit_evidence.evidence_transition_authorization`
- **Logical entity:** `evidence_transition_authorization`
- **Business purpose:** Controlled authorization/approval record for allowed evidence state transitions (release, disposal request, legal-hold change, etc. as permitted).
- **Primary key:** `evidence_transition_authorization_id uuid`
- **Candidate alternate keys:** policy-dependent.
- **Tenant ownership semantics:** Tenant-owned.
- **Lifecycle and deletion behavior:** Retained/immutable decision record.
- **Audit requirements:** Mandatory for controlled transitions.
- **Sensitive-data classification:** Highly sensitive authorization/legal metadata.
- **Shared columns:** Standard/immutable decision metadata.

| Column | PostgreSQL type | Nullability | Default | Description / constraints role |
|---|---|---|---|---|
| `evidence_transition_authorization_id` | `uuid` | NOT NULL | generated | PK. |
| `tenant_id` | `uuid` | NOT NULL | none | Tenant consistency. |
| `forensic_evidence_record_id` | `uuid` | NOT NULL | none | FK to evidence record. |
| `requested_transition` | `text` | NOT NULL | none | Transition/action requested. |
| `authorization_status` | `text` | NOT NULL | `'pending'` | pending/approved/denied/executed (proposed). |
| `authorized_by_subject_id` | `uuid` | NULL | null | Approver. |
| `authorized_at` | `timestamptz` | NULL | null | Decision time. |
| `reason` | `text` | NOT NULL | none | Justification/policy basis. |
| `legal_hold_checked` | `boolean` | NOT NULL | false | Indicates hold/policy check performed (procedural). |

- **Foreign-key relationships:** FKs to tenant, evidence record, actor.
- **Unique constraints:** policy-dependent.
- **Check constraints (proposed):** valid status.

#### `audit_evidence.ai_interaction_audit`
- **Logical entity:** `ai_interaction_audit`
- **Business purpose:** Specialized audit record for MELIRA/external AI interactions (provider/model/region, purpose, classification/consent references, outcome, minimization indicators), correlatable with operational `audit_event`.
- **Primary key:** `ai_interaction_audit_id uuid`
- **Candidate alternate keys:** correlation to request/operation ID unique as applicable.
- **Tenant ownership semantics:** Tenant-owned.
- **Lifecycle and deletion behavior:** Append-only/immutable intent; retention per policy.
- **Audit requirements:** Mandatory for AI privacy/governance traceability.
- **Sensitive-data classification:** Sensitive governance metadata; must not store prompts/responses/secrets beyond permitted minimized references.
- **Shared columns:** Immutable `created_at`/`recorded_at`.

| Column | PostgreSQL type | Nullability | Default | Description / constraints role |
|---|---|---|---|---|
| `ai_interaction_audit_id` | `uuid` | NOT NULL | generated | PK. |
| `tenant_id` | `uuid` | NOT NULL | none | FK to tenant. |
| `audit_event_id` | `uuid` | NULL | null | Correlation FK to `audit_evidence.audit_event`. |
| `provider_configuration_id` | `uuid` | NULL | null | FK to tenant AI provider configuration. |
| `actor_subject_id` | `uuid` | NULL | null | Initiating principal. |
| `purpose` | `text` | NOT NULL | none | Declared processing purpose. |
| `provider_identifier` | `text` | NULL | null | Provider recorded at interaction time (snapshot). |
| `model_identifier` | `text` | NULL | null | Model snapshot. |
| `region_identifier` | `text` | NULL | null | Region snapshot. |
| `data_classification` | `text` | NULL | null | Classification label (policy-dependent). |
| `consent_reference_id` | `uuid` | NULL | null | FK/reference to consent/policy record. |
| `request_minimization_applied` | `boolean` | NULL | null | Indicator. |
| `outcome` | `text` | NOT NULL | none | success/failure/denied/blocked. |
| `occurred_at` | `timestamptz` | NOT NULL | none | Interaction time. |
| `correlation_id` | `text` | NULL | null | Trace correlation. |
| `metadata` | `jsonb` | NULL | null | Strictly bounded non-secret metadata. |

- **Foreign-key relationships:** FKs to tenant, audit event, provider configuration, actor, consent reference.
- **Unique constraints:** none mandatory.
- **Check constraints (proposed):** valid outcome.

### 6.6 Integration and MELIRA/AI domain

#### `integration_ai.integration_configuration`
- **Logical entity:** `integration_configuration`
- **Business purpose:** Tenant-scoped integration/connector configuration with references to externally managed secrets (no plaintext credentials).
- **Primary key:** `integration_configuration_id uuid`
- **Candidate alternate keys:** (`tenant_id`, `integration_code`) or (`tenant_id`, `data_source_id`, `config_version`) unique per policy.
- **Tenant ownership semantics:** Tenant-owned.
- **Lifecycle and deletion behavior:** Versioned/effective-dated; disable/revoke rather than delete when history required.
- **Audit requirements:** Configuration and secret-reference changes auditable.
- **Sensitive-data classification:** Sensitive configuration metadata; secret references only.
- **Shared columns:** Standard shared columns.

| Column | PostgreSQL type | Nullability | Default | Description / constraints role |
|---|---|---|---|---|
| `integration_configuration_id` | `uuid` | NOT NULL | generated | PK. |
| `tenant_id` | `uuid` | NOT NULL | none | FK to tenant. |
| `integration_code` | `text` | NOT NULL | none | Integration identifier/type key. |
| `configuration_status` | `text` | NOT NULL | `'active'` | CHECK constrained. |
| `config_body` | `jsonb` | NOT NULL | `'{}'::jsonb` | Non-secret settings; validated by application/policy. |
| `secret_reference` | `text` | NULL | null | External secret-manager reference (no secret value). |
| `effective_from` | `timestamptz` | NOT NULL | none | Effective start. |
| `effective_to` | `timestamptz` | NULL | null | Effective end. |

- **Foreign-key relationships:** FK to tenant; referenced by `integration_ai.data_source`.
- **Unique constraints:** proposed (`tenant_id`, `integration_code`, `config_version`) or equivalent; include version column if modeled separately.
- **Check constraints (proposed):** valid status.

#### `integration_ai.tenant_ai_provider_configuration`
- **Logical entity:** `tenant_ai_provider_configuration`
- **Business purpose:** Explicit tenant selection of external AI SaaS provider/model/region; no silent failover, no local inference/GPU.
- **Primary key:** `tenant_ai_provider_configuration_id uuid`
- **Candidate alternate keys:** (`tenant_id`, `provider_code`, `model_code`, `region_code`, `effective_from`) or active-configuration uniqueness per policy.
- **Tenant ownership semantics:** Tenant-owned.
- **Lifecycle and deletion behavior:** Versioned/effective-dated; historical selections retained for audit.
- **Audit requirements:** Changes and effective selections auditable.
- **Sensitive-data classification:** Sensitive configuration/governance metadata.
- **Shared columns:** Standard shared columns.

| Column | PostgreSQL type | Nullability | Default | Description / constraints role |
|---|---|---|---|---|
| `tenant_ai_provider_configuration_id` | `uuid` | NOT NULL | generated | PK. |
| `tenant_id` | `uuid` | NOT NULL | none | FK to tenant. |
| `provider_code` | `text` | NOT NULL | none | Explicit provider identifier. |
| `model_code` | `text` | NOT NULL | none | Explicit model identifier. |
| `region_code` | `text` | NULL | null | Explicit region/endpoint region if applicable. |
| `configuration_status` | `text` | NOT NULL | `'active'` | CHECK constrained. |
| `is_default` | `boolean` | NOT NULL | false | Default selection flag (policy-governed). |
| `effective_from` | `timestamptz` | NOT NULL | none | Effective start. |
| `effective_to` | `timestamptz` | NULL | null | Effective end. |
| `policy_notes_ref` | `text` | NULL | null | Reference to approved policy/terms context. |

- **Foreign-key relationships:** FK to tenant; referenced by secret references, consent/policy refs, usage accounting, AI interaction audit.
- **Unique constraints:** policy-dependent uniqueness for active/default config.
- **Check constraints (proposed):** valid status; effective window consistency.

#### `integration_ai.ai_provider_secret_reference`
- **Logical entity:** `ai_provider_secret_reference`
- **Business purpose:** Reference to externally managed AI provider credential/secret (secret-manager/KMS); never stores plaintext secret.
- **Primary key:** `ai_provider_secret_reference_id uuid`
- **Candidate alternate keys:** (`tenant_id`, `provider_configuration_id`, `secret_purpose`) unique as applicable.
- **Tenant ownership semantics:** Tenant-owned.
- **Lifecycle and deletion behavior:** Rotation/versioning via new references or version fields; revoke/disable retained.
- **Audit requirements:** Creation, rotation, revocation, and access-governance events auditable (access audited at application boundary).
- **Sensitive-data classification:** Highly sensitive reference metadata (not secret value).
- **Shared columns:** Standard shared columns.

| Column | PostgreSQL type | Nullability | Default | Description / constraints role |
|---|---|---|---|---|
| `ai_provider_secret_reference_id` | `uuid` | NOT NULL | generated | PK. |
| `tenant_id` | `uuid` | NOT NULL | none | FK to tenant. |
| `provider_configuration_id` | `uuid` | NOT NULL | none | FK to provider configuration. |
| `secret_purpose` | `text` | NOT NULL | none | e.g. api_key/credential. |
| `secret_manager_ref` | `text` | NOT NULL | none | External secret locator/reference. |
| `reference_status` | `text` | NOT NULL | `'active'` | CHECK constrained. |
| `rotated_at` | `timestamptz` | NULL | null | Rotation time. |

- **Foreign-key relationships:** FKs to tenant and provider configuration.
- **Unique constraints:** proposed uniqueness per configuration/purpose.
- **Check constraints (proposed):** valid status; non-empty secret reference.

#### `integration_ai.ai_provider_policy_consent_reference`
- **Logical entity:** `ai_provider_policy_consent_reference`
- **Business purpose:** Records consent, policy, classification, and terms references governing external AI data transmission/usage.
- **Primary key:** `ai_provider_policy_consent_reference_id uuid`
- **Candidate alternate keys:** (`tenant_id`, `provider_configuration_id`, `policy_type`, `effective_from`) unique.
- **Tenant ownership semantics:** Tenant-owned.
- **Lifecycle and deletion behavior:** Effective-dated/versioned; retained for compliance/audit.
- **Audit requirements:** Grant/revocation/updates auditable.
- **Sensitive-data classification:** Compliance/governance-sensitive metadata.
- **Shared columns:** Standard shared columns.

| Column | PostgreSQL type | Nullability | Default | Description / constraints role |
|---|---|---|---|---|
| `ai_provider_policy_consent_reference_id` | `uuid` | NOT NULL | generated | PK. |
| `tenant_id` | `uuid` | NOT NULL | none | FK to tenant. |
| `provider_configuration_id` | `uuid` | NULL | null | FK to provider configuration (nullable if tenant-level policy). |
| `policy_type` | `text` | NOT NULL | none | Consent/terms/classification policy type. |
| `policy_reference` | `text` | NOT NULL | none | Document/version/record reference. |
| `consent_status` | `text` | NOT NULL | none | granted/denied/revoked/pending (CHECK). |
| `effective_from` | `timestamptz` | NOT NULL | none | Effective start. |
| `effective_to` | `timestamptz` | NULL | null | Effective end. |
| `granted_by_subject_id` | `uuid` | NULL | null | Actor. |

- **Foreign-key relationships:** FKs to tenant, provider configuration, actor; referenced by AI interaction audit.
- **Unique constraints:** proposed per tenant/config/type/effective window.
- **Check constraints (proposed):** valid status/window.

#### `integration_ai.ai_usage_budget_accounting`
- **Logical entity:** `ai_usage_budget_accounting`
- **Business purpose:** Tracks AI usage and budget/quota accounting for external provider interactions (policy/measurement open).
- **Primary key:** `ai_usage_budget_accounting_id uuid`
- **Candidate alternate keys:** (`tenant_id`, `provider_configuration_id`, `accounting_period_start`) or idempotent event reference unique.
- **Tenant ownership semantics:** Tenant-owned.
- **Lifecycle and deletion behavior:** Append/update per accounting model; retained for governance/billing support as applicable.
- **Audit requirements:** Adjustments and reconciliations auditable.
- **Sensitive-data classification:** Commercial/governance-sensitive.
- **Shared columns:** Standard shared columns.

| Column | PostgreSQL type | Nullability | Default | Description / constraints role |
|---|---|---|---|---|
| `ai_usage_budget_accounting_id` | `uuid` | NOT NULL | generated | PK. |
| `tenant_id` | `uuid` | NOT NULL | none | FK to tenant. |
| `provider_configuration_id` | `uuid` | NULL | null | FK to provider configuration. |
| `accounting_period_start` | `timestamptz` | NOT NULL | none | Period start. |
| `accounting_period_end` | `timestamptz` | NULL | null | Period end. |
| `usage_units` | `numeric(20,6)` | NOT NULL | 0 | Measured usage units (unit definition open). |
| `budget_units` | `numeric(20,6)` | NULL | null | Budget/cap allocation if applicable. |
| `currency_or_unit_code` | `text` | NULL | null | Unit/currency context. |
| `last_interaction_audit_id` | `uuid` | NULL | null | Correlation to latest contributing interaction. |

- **Foreign-key relationships:** FKs to tenant, provider configuration, AI interaction audit.
- **Unique constraints:** proposed per tenant/config/period.
- **Check constraints (proposed):** non-negative usage/budget values where applicable.

### 6.7 SOC and operational reference domain

#### `soc.alert`
- **Logical entity:** `alert`
- **Business purpose:** Detection-generated alert associated with tenant assets/events/findings/incidents.
- **Primary key:** `alert_id uuid`
- **Candidate alternate keys:** (`tenant_id`, `external_alert_reference`) unique when provided.
- **Tenant ownership semantics:** Tenant-owned.
- **Lifecycle and deletion behavior:** Open/acknowledged/in-progress/resolved/suppressed/closed states; retained per policy.
- **Audit requirements:** Status/assignment/triage actions auditable.
- **Sensitive-data classification:** Security-sensitive operational data.
- **Shared columns:** Standard shared columns.

| Column | PostgreSQL type | Nullability | Default | Description / constraints role |
|---|---|---|---|---|
| `alert_id` | `uuid` | NOT NULL | generated | PK. |
| `tenant_id` | `uuid` | NOT NULL | none | FK to tenant. |
| `asset_id` | `uuid` | NULL | null | FK to asset. |
| `security_event_id` | `uuid` | NULL | null | FK to triggering event. |
| `incident_case_id` | `uuid` | NULL | null | FK to linked case. |
| `detection_rule_version_id` | `uuid` | NULL | null | FK to rule version. |
| `alert_status` | `text` | NOT NULL | `'open'` | CHECK constrained. |
| `severity` | `text` | NULL | null | Severity classification. |
| `title` | `text` | NOT NULL | none | Summary. |
| `detected_at` | `timestamptz` | NOT NULL | none | Detection time. |
| `details` | `jsonb` | NULL | null | Bounded alert context. |

- **Foreign-key relationships:** FKs to tenant, asset, security event, incident case, detection rule version.
- **Unique constraints:** optional external alert reference uniqueness.
- **Check constraints (proposed):** valid status.

#### `soc.incident_case`
- **Logical entity:** `incident_case`
- **Business purpose:** Investigation/response case container linking alerts, assets, evidence, and actions.
- **Primary key:** `incident_case_id uuid`
- **Candidate alternate keys:** (`tenant_id`, `case_number`) unique if assigned.
- **Tenant ownership semantics:** Tenant-owned.
- **Lifecycle and deletion behavior:** Open/contained/resolved/closed states; retained.
- **Audit requirements:** Case actions and evidence links auditable.
- **Sensitive-data classification:** Highly sensitive security/incident data.
- **Shared columns:** Standard shared columns.

| Column | PostgreSQL type | Nullability | Default | Description / constraints role |
|---|---|---|---|---|
| `incident_case_id` | `uuid` | NOT NULL | generated | PK. |
| `tenant_id` | `uuid` | NOT NULL | none | FK to tenant. |
| `case_number` | `text` | NULL | null | Human/reference identifier. |
| `case_status` | `text` | NOT NULL | `'open'` | CHECK constrained. |
| `severity` | `text` | NULL | null | Case severity. |
| `title` | `text` | NOT NULL | none | Summary. |
| `opened_at` | `timestamptz` | NOT NULL | none | Open time. |
| `closed_at` | `timestamptz` | NULL | null | Close time. |
| `summary` | `text` | NULL | null | Controlled summary. |

- **Foreign-key relationships:** FK to tenant; referenced by alerts and evidence/correlation records.
- **Unique constraints:** proposed unique case number per tenant.
- **Check constraints (proposed):** valid status and closure consistency.

#### `soc.detection_rule`
- **Logical entity:** `detection_rule`
- **Business purpose:** Detection rule definition metadata (tenant-specific or managed catalog scope as proposed).
- **Primary key:** `detection_rule_id uuid`
- **Candidate alternate keys:** (`tenant_id` or scope, `rule_code`) unique.
- **Tenant ownership semantics:** Tenant-owned or managed/global-scope depending on deployment model (Proposed; default tenant-owned unless explicitly global-managed).
- **Lifecycle and deletion behavior:** Enabled/disabled/retired; version history via `detection_rule_version`.
- **Audit requirements:** Rule lifecycle changes auditable.
- **Sensitive-data classification:** Security-sensitive logic metadata.
- **Shared columns:** Standard shared columns.

| Column | PostgreSQL type | Nullability | Default | Description / constraints role |
|---|---|---|---|---|
| `detection_rule_id` | `uuid` | NOT NULL | generated | PK. |
| `tenant_id` | `uuid` | NULL | null | Tenant scope when tenant-owned; NULL only if explicitly global-managed (must be controlled). |
| `rule_code` | `text` | NOT NULL | none | Stable rule identifier. |
| `rule_name` | `text` | NOT NULL | none | Name. |
| `rule_status` | `text` | NOT NULL | `'active'` | CHECK constrained. |
| `description` | `text` | NULL | null | Purpose. |

- **Foreign-key relationships:** Optional FK to tenant; referenced by `detection_rule_version`.
- **Unique constraints:** proposed per-scope unique rule code.
- **Check constraints (proposed):** valid status.

#### `soc.detection_rule_version`
- **Logical entity:** `detection_rule_version`
- **Business purpose:** Immutable/versioned snapshot of detection rule logic/configuration.
- **Primary key:** `detection_rule_version_id uuid`
- **Candidate alternate keys:** (`detection_rule_id`, `version_number`) unique.
- **Tenant ownership semantics:** Inherits scope from parent rule.
- **Lifecycle and deletion behavior:** Immutable historical versions.
- **Audit requirements:** Publication/activation auditable.
- **Sensitive-data classification:** Security-sensitive.
- **Shared columns:** Immutable `created_at`.

| Column | PostgreSQL type | Nullability | Default | Description / constraints role |
|---|---|---|---|---|
| `detection_rule_version_id` | `uuid` | NOT NULL | generated | PK. |
| `detection_rule_id` | `uuid` | NOT NULL | none | FK to `soc.detection_rule`. |
| `version_number` | `integer` | NOT NULL | none | Monotonic version. |
| `rule_definition` | `jsonb` | NOT NULL | none | Structured rule definition/parameters (validated). |
| `effective_from` | `timestamptz` | NOT NULL | none | Effective start. |
| `effective_to` | `timestamptz` | NULL | null | Effective end. |
| `created_at` | `timestamptz` | NOT NULL | `now()` proposed | Creation time. |

- **Foreign-key relationships:** FK to detection rule; referenced by alerts.
- **Unique constraints:** `uq_detection_rule_version` on (`detection_rule_id`, `version_number`).
- **Check constraints (proposed):** `version_number > 0`.

#### `soc.vulnerability_finding`
- **Logical entity:** `vulnerability_finding`
- **Business purpose:** Records vulnerability/exposure findings associated with assets and observations.
- **Primary key:** `vulnerability_finding_id uuid`
- **Candidate alternate keys:** (`tenant_id`, `source_finding_reference`) unique when provided.
- **Tenant ownership semantics:** Tenant-owned.
- **Lifecycle and deletion behavior:** Open/confirmed/remediated/accepted/risk-accepted/closed states; retained.
- **Audit requirements:** Triage/remediation/status changes auditable.
- **Sensitive-data classification:** Security-sensitive.
- **Shared columns:** Standard shared columns.

| Column | PostgreSQL type | Nullability | Default | Description / constraints role |
|---|---|---|---|---|
| `vulnerability_finding_id` | `uuid` | NOT NULL | generated | PK. |
| `tenant_id` | `uuid` | NOT NULL | none | FK to tenant. |
| `asset_id` | `uuid` | NULL | null | FK to asset. |
| `asset_inventory_observation_id` | `uuid` | NULL | null | FK to observation. |
| `finding_status` | `text` | NOT NULL | `'open'` | CHECK constrained. |
| `severity` | `text` | NULL | null | Severity. |
| `finding_type` | `text` | NOT NULL | none | Category/type. |
| `source_finding_reference` | `text` | NULL | null | External/scanner reference. |
| `detected_at` | `timestamptz` | NOT NULL | none | Detection time. |
| `details` | `jsonb` | NULL | null | Bounded details. |

- **Foreign-key relationships:** FKs to tenant, asset, inventory observation.
- **Unique constraints:** optional source reference uniqueness.
- **Check constraints (proposed):** valid status.

#### `soc.threat_intelligence_reference`
- **Logical entity:** `threat_intelligence_reference`
- **Business purpose:** Global/shared threat intelligence indicator or reference catalog entry usable in tenant-scoped detections/correlations.
- **Primary key:** `threat_intelligence_reference_id uuid`
- **Candidate alternate keys:** (`source_name`, `external_reference`) unique.
- **Tenant ownership semantics:** Platform-global/shared catalog; tenant usage must be linked through tenant-scoped records/queries without exposing other tenants' data.
- **Lifecycle and deletion behavior:** Active/deprecated/retired; historical references retained as needed.
- **Audit requirements:** Catalog updates auditable.
- **Sensitive-data classification:** Security intelligence metadata; sensitivity depends on content.
- **Shared columns:** Standard shared columns.

| Column | PostgreSQL type | Nullability | Default | Description / constraints role |
|---|---|---|---|---|
| `threat_intelligence_reference_id` | `uuid` | NOT NULL | generated | PK. |
| `source_name` | `text` | NOT NULL | none | Intelligence source. |
| `reference_type` | `text` | NOT NULL | none | Indicator/reference type. |
| `external_reference` | `text` | NOT NULL | none | External ID/value reference. |
| `confidence` | `text` | NULL | null | Confidence classification. |
| `status` | `text` | NOT NULL | `'active'` | CHECK constrained. |
| `published_at` | `timestamptz` | NULL | null | Source publication time. |
| `metadata` | `jsonb` | NULL | null | Bounded metadata. |

- **Foreign-key relationships:** May be referenced by tenant-scoped SOC records through explicit link columns/tables if introduced (none required now beyond design allowance).
- **Unique constraints:** `uq_threat_intel_source_ref` on (`source_name`, `external_reference`).
- **Check constraints (proposed):** valid status.

#### `soc.asset_inventory_observation`
- **Logical entity:** `asset_inventory_observation`
- **Business purpose:** Point-in-time inventory observation/snapshot of an asset as reported by a data source.
- **Primary key:** `asset_inventory_observation_id uuid`
- **Candidate alternate keys:** (`tenant_id`, `data_source_id`, `asset_id`, `observed_at`, `observation_hash`) policy-dependent uniqueness to reduce duplicates.
- **Tenant ownership semantics:** Tenant-owned.
- **Lifecycle and deletion behavior:** Append-oriented/time-series-like observations; retention/partitioning candidates.
- **Audit requirements:** Provenance traceable to source/receipt.
- **Sensitive-data classification:** Potentially sensitive asset/system inventory data.
- **Shared columns:** Immutable `created_at`.

| Column | PostgreSQL type | Nullability | Default | Description / constraints role |
|---|---|---|---|---|
| `asset_inventory_observation_id` | `uuid` | NOT NULL | generated | PK. |
| `tenant_id` | `uuid` | NOT NULL | none | FK to tenant. |
| `asset_id` | `uuid` | NULL | null | FK to asset (nullable if unresolved at observation time). |
| `data_source_id` | `uuid` | NOT NULL | none | FK to data source. |
| `event_receipt_id` | `uuid` | NULL | null | FK to receipt/provenance. |
| `observed_at` | `timestamptz` | NOT NULL | none | Observation time. |
| `observation_hash` | `text` | NULL | null | Optional dedupe/content hash. |
| `inventory_attributes` | `jsonb` | NULL | null | Structured inventory snapshot; justified JSONB use with minimization. |

- **Foreign-key relationships:** FKs to tenant, asset, data source, event receipt.
- **Unique constraints:** optional policy-dependent dedupe uniqueness.
- **Check constraints (proposed):** observation time present.

## 7. JSONB usage justification (Section E element)

| Table.column | Purpose | Structure/validation expectation | Query/indexing considerations | Evolution/sensitivity notes |
|---|---|---|---|---|
| `core.tenant.metadata` | Limited administrative non-authoritative metadata | Small object, application-validated keys | Rarely queried; avoid indexing sensitive fields | No secrets/authorization authority. |
| `core.support_access_grant.access_scope` | Structured scoped permissions/constraints | Explicit schema/allowed keys required | Queried by grant checks; targeted expression/GIN indexing only if justified | Highly sensitive; minimize. |
| `core.tenant_configuration.config_body` | Versioned domain configuration payload | Domain-specific validation required | Filter by domain/version columns, not arbitrary JSON paths by default | No secrets. |
| `core.asset.attributes`, `core.asset_identity_claim.claim_payload`, `core.asset_lifecycle_event.details` | Limited descriptive/provenance details | Bounded, validated/minimized | Avoid hot-path dependence; index selectively if proven | Must not become authoritative identity/licensing truth. |
| `ingest.event_receipt.normalized_payload`, `ingest.security_event.normalized_attributes` | Bounded normalized subsets (not full raw payload default) | Schema-reference-aligned validation | Potential expression/GIN indexes for proven query patterns; consider partitioning/retention | Sensitive telemetry minimization; prefer references to large raw objects. |
| `processing.outbox_message.payload`, `processing.processing_work_item.payload` | Minimal dispatch/coordination payloads | Strict contract per message/work type | Usually fetched by key/state, not ad hoc JSON search | No secrets/sensitive external payload duplication. |
| `audit_evidence.*.details/metadata` | Bounded non-secret audit/custody context | Controlled keys, minimization required | Rarely searched deeply; index only proven fields | Exclude secrets and unnecessary PII. |
| `integration_ai.integration_configuration.config_body` | Non-secret integration settings | Connector-specific validation | Keyed by config identity/version | Secret references separate. |
| `soc.*.details/rule_definition/inventory_attributes/metadata` | Bounded SOC/rule/observation structures | Validated schemas; rule definitions versioned | Selective indexing for known query paths; volume considerations for observations | Security-sensitive content controls required. |

**General policy (proposed):** core identifiers, relationships, lifecycle states, tenancy, idempotency keys, dedup namespaces, and accounting authorities remain relational columns/constraints. JSONB is not used to bypass normalization or integrity for authoritative relationships.

## 8. Logical-to-physical traceability completeness

- All mapped logical entities in §3.3 are specified as proposed physical tables in §6.1–§6.7, including entities simplified/omitted from logical ERDs (`external_identity_subject`, `role_permission`, `membership_role_assignment`, `support_access_approval`, `source_device_key` optional projection, `source_device_fingerprint_alias`, `asset_identity_claim`, `identity_resolution_case`, `asset_tombstone`, `processing_work_item` optional, `evidence_object_version`, `evidence_custody_event`, `evidence_transition_authorization`, `ai_usage_budget_accounting`).
- **Representation exceptions (explicit, bounded):** `source_device_key` may be non-materialized with binding-owned authoritative attributes (1:1 dependent projection if materialized); `processing_work_item` is optional/non-core coordination and may remain unused without replacing receipt/outbox truth. No other logical entity is omitted or merged away without documented mapping.
- Detailed cross-document traceability and unresolved items are compiled in [POSTGRESQL_PHYSICAL_SCHEMA_ROUND2_FINAL_REVIEW.md](./POSTGRESQL_PHYSICAL_SCHEMA_ROUND2_FINAL_REVIEW.md).

## 9. Assumptions and limitations

- All specifications are **Proposed/NOT IMPLEMENTED/NOT TESTED**. Exact CHECK value sets, partial-index predicates, composite-FK compositions, and trigger/procedural enforcement (where needed for complex invariants/overlaps) require implementation review and validation.
- Counter/entitlement accounting formulas (OD-001/003/004), binding uniqueness finalization (OD-002), idempotency contract approval (OD-008), dedup fallback details (OD-013), merge/split authority/licensing effects (OD-005), fingerprint protection/rotation (OD-006/007), outbox leasing/fencing/unknown-outcome policy (OD-009), retention/legal hold (OD-010), AI governance details (OD-011), and retention/workload validation (OD-012) remain open/deferred as recorded.
- No performance, capacity, or production-readiness claims are made.
