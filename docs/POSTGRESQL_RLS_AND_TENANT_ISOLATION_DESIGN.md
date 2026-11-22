# CARES PostgreSQL RLS and Tenant Isolation Design (Round 2)

**Status:** Proposed design documentation only; **NOT IMPLEMENTED, NOT TESTED**. This document defines the physical isolation model, role posture, tenant-context lifecycle, and conceptual RLS policy design for CARES PostgreSQL. No database roles, grants, RLS policies, security-definer functions, GUC settings, or enforcement objects are created. **RLS is defense in depth and not sufficient alone**; application/service authorization remains required.

**Non-negotiable rules (preserved):** tenant authority comes only from trusted, verified, transaction-bound context; **never** from client-supplied tenant IDs and **never** from user-settable PostgreSQL GUCs for authorization decisions. Cross-tenant reads/writes/joins/references/indirect leakage must be prevented.

## 1. Tenant-scoped and global tables

### 1.1 Tenant-owned tables (RLS-protected, tenant-context required)

| Schema | Table | `tenant_id` | Notes |
|---|---|---|---|
| core | `tenant_membership` | NOT NULL | Tenant-scoped membership records. |
| core | `membership_role_assignment` | NOT NULL | Tenant/membership scoped assignments. |
| core | `support_access_grant` | `target_tenant_id` NOT NULL | Tenant-contextual target scope. |
| core | `support_access_approval` | `target_tenant_id` NOT NULL | Grant/tenant contextual. |
| core | `tenant_configuration` | NOT NULL | Canonical tenant config. |
| core | `asset` | NOT NULL | Canonical tenant asset. |
| core | `asset_data_source` | NOT NULL | Authoritative stable binding. |
| core | `source_device_key` | NOT NULL | Optional dependent projection (if materialized). |
| core | `source_device_fingerprint_alias` | NOT NULL | Alias/lookup records. |
| core | `asset_identity_claim` | NOT NULL | Provenance claims. |
| core | `identity_resolution_case` | NOT NULL | Resolution workflow. |
| core | `asset_lifecycle_event` | NOT NULL | History. |
| core | `asset_merge_operation` | NOT NULL | Operation record. |
| core | `asset_split_operation` | NOT NULL | Operation record. |
| core | `asset_lineage_link` | NOT NULL | Typed lineage. |
| core | `subscription_entitlement` | NOT NULL | Entitlement terms. |
| core | `tenant_license_usage_state` | NOT NULL | Usage/capacity state. |
| core | `asset_license_event` | NOT NULL | Licensing history. |
| core | `identity_operation_idempotency_ledger` | NOT NULL | Identity/licensing idempotency. |
| core | `asset_license_reservation` | NOT NULL | Reservation records. |
| core | `asset_tombstone` | NOT NULL | Terminal historical record. |
| ingest | `event_receipt` | NOT NULL | Ingestion/dedup. |
| ingest | `security_event` | NOT NULL | Normalized event. |
| processing | `outbox_message` | NULLable by model but expected tenant-scoped; policy required | Tenant-contextual async work; global control-plane messages, if ever introduced, must be explicitly separated and justified. |
| processing | `outbox_attempt` | NULLable via message context | Inherits/aligns with message tenant scope. |
| processing | `processing_work_item` | NULLable when applicable | Optional/non-core; tenant-scoped when used. |
| audit_evidence | `audit_event` | NULLable for explicitly platform-level actions (tightly controlled) | Prefer tenant-scoped; platform-level audit requires separate controlled access path. |
| audit_evidence | `ai_interaction_audit` | NOT NULL | Tenant AI governance audit. |
| audit_evidence | `forensic_evidence_record` | NOT NULL | Tenant evidence metadata. |
| audit_evidence | `evidence_object_version` | NOT NULL | Tenant consistency. |
| audit_evidence | `evidence_custody_event` | NOT NULL | Tenant consistency. |
| audit_evidence | `evidence_transition_authorization` | NOT NULL | Tenant consistency. |
| integration_ai | `data_source` | NOT NULL | Tenant connector instance. |
| integration_ai | `integration_configuration` | NOT NULL | Tenant integration config. |
| integration_ai | `tenant_ai_provider_configuration` | NOT NULL | Explicit tenant provider selection. |
| integration_ai | `ai_provider_secret_reference` | NOT NULL | Tenant secret references only. |
| integration_ai | `ai_provider_policy_consent_reference` | NOT NULL | Consent/policy refs. |
| integration_ai | `ai_usage_budget_accounting` | NOT NULL | Usage/budget accounting. |
| soc | `alert` | NOT NULL | Tenant SOC record. |
| soc | `incident_case` | NOT NULL | Tenant SOC record. |
| soc | `vulnerability_finding` | NOT NULL | Tenant SOC record. |
| soc | `asset_inventory_observation` | NOT NULL | Tenant observation. |
| soc | `detection_rule` | NULLable (tenant-owned default; global-managed only if explicitly controlled) | Scope must be explicit; global-managed rules require separate governance and must not expose tenant data. |
| soc | `detection_rule_version` | follows parent rule scope | Access controlled via rule scope. |

### 1.2 Platform-global or catalog-scoped tables (no tenant row ownership / special access control)

| Schema | Table | Scope | Access posture (proposed) |
|---|---|---|---|
| core | `tenant` | Global tenant registry/root | Controlled administrative/runtime access; not exposed via tenant-context RLS in the same way as tenant-owned rows (except self-tenant reads through verified context where appropriate). |
| core | `external_identity_subject` | Global identity principal | Controlled access; linked to tenants via memberships and verified authorization. |
| core | `role` | Global/system and optionally tenant-defined | System roles global-read controlled; tenant-defined roles (if `tenant_id` set) treated as tenant-scoped. |
| core | `role_permission` | Follows role scope | Access governed by role scope/administration paths. |
| ingest | `event_schema_reference` | Global/shared catalog (proposed) | Read access for validation/normalization; write restricted to controlled roles. |
| soc | `threat_intelligence_reference` | Global/shared catalog | Read access controlled; no tenant data embedded. |

**Design note:** global/catalog tables must never become a path for cross-tenant data leakage; joins from tenant-owned tables to global catalogs are permitted only on non-tenant reference data and must not bypass tenant predicates on tenant-owned sides.

## 2. Tenant context propagation (conceptual)

### 2.1 Trusted, verified, transaction-bound context

1. **Authentication/authorization upstream:** request/job identity and tenant entitlement are established by trusted application services using verified identity and authorization inputs (not raw client claims).
2. **Verification:** before tenant-scoped database work, a trusted verifier validates the tenant/scope assertion and binds it to an auditable, transaction-scoped context (e.g. a protected verified-context record/token validated by hardened helper logic). The exact mechanism is implementation-specific but must be non-forgeable by unprivileged runtime roles.
3. **Transaction scope:** each tenant-scoped database transaction establishes its own verified context and clears it at transaction end. Context **must not** leak across pooled connections, transactions, or sessions.
4. **Database enforcement:** RLS and any authorization helpers read tenant/scope decisions only from trusted verified context (hardened, narrowly scoped security helpers/internal structures as approved). **PostgreSQL custom GUCs settable by user/session (e.g. `SET app.tenant_id`/`current_setting`) are explicitly disallowed as authorization authority**; they may be used only for non-authoritative diagnostics if separately approved and never consulted by RLS/authorization decisions.
5. **Fail closed:** missing, invalid, expired, mismatched, or unverified context results in denial/no rows/no writes for tenant-protected operations.

### 2.2 Connection pooling and session state

- Pooled connections are untrusted carriers of prior session state; application/runtime must guarantee context reset and transaction-local establishment on every checkout/use.
- Use transaction-scoped context patterns only (conceptually: establish at begin, clear on commit/rollback/failure). Avoid session-persistent tenant context for authorization.
- Background workers, ingest processors, outbox claimers, and admin jobs must each establish verified context appropriate to their scope (tenant-specific job context, or explicitly controlled non-tenant administrative context) per execution unit.

### 2.3 Background jobs and administrative operations

- **Tenant-scoped jobs/workers:** run under least-privilege runtime roles with verified tenant context per job/transaction; RLS applies.
- **Controlled administrative/support operations:** time-bound, scoped, reasoned, and audited (e.g. `support_access_grant`/approval flow); may use explicitly approved elevated/control-plane procedures but **not** routine `BYPASSRLS` runtime paths and not blanket tenant access. Any exceptional bypass must be separately authorized, minimal, logged, and reviewed.
- **Migration/maintenance roles:** separate from runtime roles; no ordinary request traffic; maintenance must not silently bypass legal hold/evidence/retention controls.

## 3. Conceptual RLS model

### 3.1 Policy posture (proposed)

- Enable and enforce RLS on all tenant-owned/protected tables as applicable (`ENABLE ROW LEVEL SECURITY`; `FORCE ROW LEVEL SECURITY` considered where ownership/role design permits and does not break controlled administrative paths) — exact applicability requires implementation review.
- **Restrictive tenant-boundary predicate (conceptual):** tenant-owned rows visible/mutable only when `row.tenant_id` (or equivalent target tenant key) matches the verified tenant from trusted transaction-bound context and required scope/action checks pass.
- **Permissive/action policies (conceptual, if used):** may refine allowed operations (select/insert/update/delete) by role/scope but must never weaken tenant boundary; restrictive and permissive policies combine according to PostgreSQL semantics and must be designed/tested explicitly.
- **Command-specific enforcement:** `SELECT`, `INSERT`, `UPDATE`, `DELETE` policies/privileges defined per table/use case; `INSERT`/`UPDATE` must enforce `WITH CHECK`-equivalent tenant consistency so rows cannot be written into another tenant. `UPDATE ... RETURNING`/row-addressed workflows require explicit visibility/read qualification design.
- **Default deny/fail-closed:** no verified context => no access.

### 3.2 Role and privilege model (proposed)

| Role (conceptual) | Purpose | Privileges (high level) | Prohibitions |
|---|---|---|---|
| schema/migration owner roles (NOLOGIN/controlled) | DDL, ownership, migration execution | Controlled schema/object ownership and migration privileges | Not used for ordinary runtime traffic. |
| `cares_api_runtime` | Tenant-scoped API/application operations | Least-privilege DML/SELECT on approved objects/paths; execute approved narrow helpers | No `BYPASSRLS`, no schema/security ownership, no direct security-internal table writes except approved paths. |
| `cares_ingest_runtime` | Ingestion/acceptance processing | Least-privilege ingest-path operations | Same prohibitions; no broad admin. |
| `cares_worker_runtime` | Outbox/async/background processing | Least-privilege worker-path operations | No evidence/security bypass, no ownership. |
| `cares_readonly_support` (if needed) | Time-bound scoped read support under audited grant | Narrow read-only approved paths | No write, no bypass, no blanket access. |
| `cares_maintenance` | Controlled maintenance/partition/reconciliation tasks | Narrow maintenance privileges under procedures | No routine authorization bypass; audited/change-controlled. |

- Runtime roles must not own protected tables, RLS policies, or security-critical functions. Security-definer helpers, if any, must be hardened (fixed `search_path`, minimal grants, narrow return values) and reviewed.
- Direct access to partition children/internal security structures should be restricted; ordinary access through approved parent/table paths.

## 4. Additional enforcement needs beyond RLS

RLS alone does not guarantee all invariants. The physical design additionally relies on:

- **Tenant-consistent composite FKs/unique constraints:** ensure child rows reference parent rows in the same tenant (especially for surrogate PK relationships) and prevent cross-tenant relationship injection.
- **Unique/idempotency/dedup constraints:** enforce ledger scope `(tenant_id, operation_type, idempotency_key)`, event receipt namespace uniqueness, binding/fingerprint uniqueness, and tombstone/lineage integrity under concurrency.
- **CHECK constraints and typed references:** enforce state vocabularies, non-negative counters, mutual exclusivity for typed lineage operation references, and temporal/basic structural rules.
- **Transactional application logic with safe SQL:** parameterized queries, verified authorization checks before writes, deterministic conflict handling, and no reliance on client-supplied tenant identifiers.
- **Controlled transition procedures:** merge/split, evidence transitions, support access activation, and licensing adjustments executed through audited, transactional, authorized paths.
- **Audit logging and monitoring:** detection of policy violations, suspicious cross-scope access attempts, reconciliation anomalies, and unknown-outcome processing.

## 5. Assumptions, risks, and validation

- **Assumptions:** supported PostgreSQL version/features, secure pooling/reset behavior, controlled security schema ownership, and availability of hardened verified-context helper implementation are required but not yet validated.
- **Risks:** misconfigured pooling can leak session state; incorrect policy/role design can permit leakage or denial; missing composite tenant FKs can allow cross-tenant references even when RLS filters reads; global/shared tables and administrative paths require strict governance.
- **Isolation testing requirements (design intent):** cross-tenant negative tests for SELECT/INSERT/UPDATE/DELETE/JOIN/RETURNING, pooled-connection context-reset tests, role/privilege tests (including no `BYPASSRLS` for runtime roles), partition access tests if partitioned, support-access scope tests, and fail-closed tests for missing/invalid context. All are **NOT IMPLEMENTED/NOT TESTED** in this round.
