# CARES PostgreSQL Round 3 Implementation Work Breakdown

**Status:** Proposed planning artifact only; **NOT IMPLEMENTED, NOT TESTED, NOT APPROVED FOR EXECUTION**. This work breakdown decomposes the bounded implementation plan into traceable work packages. It does not authorize implementation and does not create DDL/migrations/DB objects/code.

**Related documents:** [POSTGRESQL_ROUND3_IMPLEMENTATION_PLAN.md](./POSTGRESQL_ROUND3_IMPLEMENTATION_PLAN.md), [POSTGRESQL_ROUND3_MIGRATION_AND_DEPLOYMENT_STRATEGY.md](./POSTGRESQL_ROUND3_MIGRATION_AND_DEPLOYMENT_STRATEGY.md), [POSTGRESQL_ROUND3_TEST_AND_ACCEPTANCE_PLAN.md](./POSTGRESQL_ROUND3_TEST_AND_ACCEPTANCE_PLAN.md), [POSTGRESQL_ROUND3_READINESS_AND_BLOCKER_MATRIX.md](./POSTGRESQL_ROUND3_READINESS_AND_BLOCKER_MATRIX.md), [POSTGRESQL_ROUND3_DEPENDENCY_MAP.md](./POSTGRESQL_ROUND3_DEPENDENCY_MAP.md), [POSTGRESQL_ROUND3_CHANGELOG.md](./POSTGRESQL_ROUND3_CHANGELOG.md), [POSTGRESQL_ROUND3_FINAL_REVIEW.md](./POSTGRESQL_ROUND3_FINAL_REVIEW.md).

## 1. Work breakdown structure (WBS)

| WBS ID | Increment | Work package | Key deliverables (future, when authorized) | Dependencies | Readiness | Primary blockers / approvals |
|---|---|---|---|---|---|---|
| WP-0.1 | I-00 | Authorization and scope control | Approved increment scope, change-control record, explicit exclusions, sign-off checklist | Round 2 baseline, this plan set | Conditionally ready | Owner authorization |
| WP-0.2 | I-00 | Environment and toolchain readiness | Target PostgreSQL version/profile selection, migration framework/process selection, non-production environment readiness, backup/PITR/restore rehearsal plan | WP-0.1 | Conditionally ready | DBA/ops readiness, PD-001 implications reviewed |
| WP-0.3 | I-00 | Security and governance preflight | Verified-context mechanism design review, role/secret handling approach, audit/legal-hold handling plan, evidence capture plan | WP-0.1 | Blocked/conditional | Security/DBA/legal/privacy as applicable |
| WP-1.1 | I-01 | Namespace and convention package | Schema creation order, naming/constraint/index conventions, type/domain/state representation decisions, extension evaluation list | WP-0.2, PD-001/002/004 | Conditionally ready | Engineering/DBA approval (PD-001/002/004) |
| WP-1.2 | I-02 | Global/catalog foundation package | `core.tenant`, `core.external_identity_subject`, `core.role`, `core.role_permission`, `ingest.event_schema_reference`, `soc.threat_intelligence_reference` structural definitions and integrity checks plan | WP-1.1 | Conditionally ready | Global/catalog access posture review |
| WP-1.3 | I-03 | Tenant-access/config foundation package | `core.tenant_membership`, `core.membership_role_assignment`, `core.support_access_grant`, `core.support_access_approval`, `core.tenant_configuration` | WP-1.2, PD-003 | Conditionally ready | Tenant-consistent FK strategy (PD-003) |
| WP-2.1 | I-04 | Canonical asset and authoritative binding package | `core.asset`, `integration_ai.data_source`, `core.asset_data_source`, optional `core.source_device_key`, `core.source_device_fingerprint_alias`, `core.asset_identity_claim` | WP-1.3, OD-002/006/007, PD-004/011 | Conditionally ready | OD-002 bounded approval, fingerprint/protection decisions |
| WP-2.2 | I-05 | Identity lifecycle/lineage package | `core.identity_resolution_case`, `core.asset_lifecycle_event`, `core.asset_merge_operation`, `core.asset_split_operation`, `core.asset_lineage_link`, `core.asset_tombstone` | WP-2.1, OD-005/007 | Conditionally ready | OD-005/007 policy inputs, typed-lineage verification |
| WP-2.3 | I-06 | Licensing/entitlement/ledger package | `core.subscription_entitlement`, `core.tenant_license_usage_state`, `core.asset_license_event`, `core.identity_operation_idempotency_ledger`, `core.asset_license_reservation` | WP-2.1/WP-2.2, OD-001/003/004/008 | Blocked for final semantics | OD-001/003/004/008 approvals; no assumed accounting semantics |
| WP-3.1 | I-07 | Ingestion/event package | `ingest.event_receipt`, `ingest.security_event` and required references/index predicates | WP-2.1, OD-013, PD-008 | Conditionally ready | OD-013 namespace/fallback approval per connector scope |
| WP-3.2 | I-08 | Outbox/processing package | `processing.outbox_message`, `processing.outbox_attempt`, optional `processing.processing_work_item` | WP-3.1, OD-009, PD-007 | Conditionally ready | OD-009 semantics and claim/lease validation plan |
| WP-3.3 | I-09 | Audit/evidence/AI-governance package | `audit_evidence.*`, `integration_ai.integration_configuration`, `tenant_ai_provider_configuration`, `ai_provider_secret_reference`, `ai_provider_policy_consent_reference`, `ai_usage_budget_accounting`, AI interaction audit | WP-1.3/WP-2.1/WP-3.2, OD-010/011 | Conditionally ready | Legal/privacy/security governance (OD-010/011) |
| WP-3.4 | I-10 | SOC operational package | `soc.alert`, `soc.incident_case`, `soc.detection_rule`, `soc.detection_rule_version`, `soc.vulnerability_finding`, `soc.asset_inventory_observation` | WP-2.1/WP-3.1, PD-012, OD-010/012 | Conditionally ready | Scope/governance/retention assumptions |
| WP-4.1 | I-11 | Constraint and index hardening package | Tenant-consistent composite uniques/FKs, CHECKs, partial/unique indexes, expression indexes, contention-sensitive indexes per approved subset | WP-1.2–WP-3.4, PD-003/008/009 | Conditionally ready | DB review, query/index validation plan (OD-012) |
| WP-4.2 | I-11 | Partitioning-preparation (no adoption) package | Partition-key/uniqueness compatibility review, threshold/runbook planning only for candidate tables | Lifecycle design, PD-010, OD-010/012 | Deferred | Workload/retention evidence |
| WP-5.1 | I-12 | Verified tenant-context mechanism package | Approved non-GUC, non-client-authoritative, transaction-bound context mechanism and fail-closed behavior design/implementation prep | WP-4.1, PD-005 | Blocked | Security/DBA/architecture approval |
| WP-5.2 | I-12 | Roles/privileges and RLS package | Least-privilege runtime/maintenance role model, grants, RLS enablement/policies/FORCE posture as approved | WP-5.1, PD-006 | Blocked | Security/DBA approval, negative tests |
| WP-5.3 | I-12 | Pooling/session-safety validation package | Pool checkout/reset verification, transaction-local context lifecycle, background/admin scope controls | WP-5.1/WP-5.2 | Blocked | Runtime behavior evidence in non-production |
| WP-6.1 | I-13 | Operation-aligned transactional implementation planning gate | Authorized implementation specs for Operations 1–13, idempotency coupling, outbox claim/recovery, evidence transitions | WP-5.3, OD-001/003/004/005/008/009/010/011/013 | Blocked / out of scope now | All required approvals and prior validation evidence |
| WP-6.2 | I-14 | Retention/maintenance automation planning gate | Partition adoption, purge/archive/legal-hold automation, maintenance tuning/runbooks | WP-4.2, OD-010/012 | Blocked/Deferred | Legal/compliance/ops/workload approvals |

## 2. Domain-to-entity mapping (planning traceability)

| Domain/schema | Tables (Round 2 physical baseline) | Primary increments |
|---|---|---|
| `core` tenant/access/config | `tenant`, `external_identity_subject`, `tenant_membership`, `role`, `role_permission`, `membership_role_assignment`, `support_access_grant`, `support_access_approval`, `tenant_configuration` | I-02, I-03 |
| `core` asset/identity/lineage/licensing | `asset`, `asset_data_source`, `source_device_key` (optional dependent), `source_device_fingerprint_alias`, `asset_identity_claim`, `identity_resolution_case`, `asset_lifecycle_event`, `asset_merge_operation`, `asset_split_operation`, `asset_lineage_link`, `subscription_entitlement`, `tenant_license_usage_state`, `asset_license_event`, `identity_operation_idempotency_ledger`, `asset_license_reservation`, `asset_tombstone` | I-04, I-05, I-06 |
| `ingest` | `event_schema_reference`, `event_receipt`, `security_event` | I-02, I-07 |
| `processing` | `outbox_message`, `outbox_attempt`, `processing_work_item` (optional/non-core) | I-08 |
| `audit_evidence` | `audit_event`, `forensic_evidence_record`, `evidence_object_version`, `evidence_custody_event`, `evidence_transition_authorization`, `ai_interaction_audit` | I-09 |
| `integration_ai` | `data_source`, `integration_configuration`, `tenant_ai_provider_configuration`, `ai_provider_secret_reference`, `ai_provider_policy_consent_reference`, `ai_usage_budget_accounting` | I-04, I-09 |
| `soc` | `alert`, `incident_case`, `detection_rule`, `detection_rule_version`, `vulnerability_finding`, `threat_intelligence_reference`, `asset_inventory_observation` | I-02, I-10 |

## 3. Cross-cutting work packages

| ID | Area | Planned activities (future) | Must preserve |
|---|---|---|---|
| XC-1 | Tenant isolation assurance | Design review, SQL/privilege review, negative tests, pooling tests, support-access scope tests | No client/GUC tenant authority; RLS defense-in-depth; fail-closed behavior |
| XC-2 | Idempotency and concurrency | Ledger/receipt uniqueness validation, replay/conflict/unknown-commit scenarios, lock/contention analysis | Separate ledger vs receipt semantics; no exactly-once external delivery |
| XC-3 | Audit/evidence/legal hold | Append/transition controls, custody/version integrity checks, legal-hold enforcement paths, retention class mapping | No silent rewrite/delete; controlled transitions only |
| XC-4 | Observability and operations | Migration logs/checksums, object inventory, constraint/index verification, anomaly alerts (reconciliation, unknown outcomes) | Auditable, reproducible change control |
| XC-5 | Documentation and traceability | Keep plan/WBS/matrix/map synchronized with executed evidence; record deviations/findings explicitly | No undocumented status promotion of OD/PD/ADR |

## 4. Exit criteria per work package (planning-level)

A future work package may be considered complete only when: (1) authorized scope executed in the approved environment, (2) verification evidence collected per [POSTGRESQL_ROUND3_TEST_AND_ACCEPTANCE_PLAN.md](./POSTGRESQL_ROUND3_TEST_AND_ACCEPTANCE_PLAN.md), (3) rollback/recovery posture confirmed, (4) blockers/approvals satisfied or explicitly bounded, and (5) results recorded without overstating readiness.
