# CARES PostgreSQL Index Strategy (Round 2)

**Status:** Proposed index design only; **NOT IMPLEMENTED, NOT TESTED**. Indexes are design recommendations derived from logical relationships, transaction boundaries, isolation requirements, and expected access patterns. No performance/capacity claims are made; final selection requires query-plan analysis, workload validation, and migration review.

**Baseline:** Round 1.1 logical model/audit (`c433fe8...`) and Round 2 physical schema design.

## 1. Principles and assumptions

- **Tenant-first access:** most tenant-scoped lookups and constraints include `tenant_id` as the leading key component to support tenant filtering, RLS-aligned access, and future manageability (partition-alignment assumptions to be validated).
- **Integrity before optimization:** unique indexes enforce canonical business/idempotency/dedup invariants; secondary indexes are added only for justified query patterns and must consider write amplification, storage, and maintenance (VACUUM/autovacuum, bloat).
- **Index type choice (proposed, PostgreSQL default B-tree unless noted):** B-tree for equality/range/order/prefix lookups and uniqueness; partial B-tree for state-scoped hot subsets (e.g. active/claimable rows) where predicates are stable; GIN for selective `jsonb` containment/path queries only when proven necessary; BRIN for large append-only/time-ordered tables if correlation and workload justify (deferred/conditional); GiST considered only for specialized types/ranges if introduced later.
- **No speculative broad JSON indexing:** JSONB columns are limited; any GIN/expression index must be tied to a specific, justified query path and sensitivity/minimization review.

## 2. Index inventory

| Table | Index name (proposed) | Columns (order) / expression | Unique | Partial predicate | Query pattern / purpose | Rationale and trade-offs |
|---|---|---|---|---|---|---|
| `core.tenant` | `pk_tenant` | `(tenant_id)` | Yes (PK) | none | Tenant lookup by ID | Root identity lookup. |
| `core.tenant` | `uq_tenant_slug` | `(tenant_slug)` | Yes | `WHERE tenant_slug IS NOT NULL` | Lookup by external slug | Prevents duplicate slugs; partial avoids NULL collisions. |
| `core.external_identity_subject` | `pk_external_identity_subject` | `(external_identity_subject_id)` | Yes | none | Principal lookup | PK access. |
| `core.external_identity_subject` | `uq_external_identity_subject_issuer_subject` | `(issuer, subject)` | Yes | none | IdP subject resolution | Required for deterministic external identity mapping. |
| `core.tenant_membership` | `pk_tenant_membership` | `(tenant_membership_id)` | Yes | none | Membership lookup | PK access. |
| `core.tenant_membership` | `ix_tenant_membership_tenant_subject` | `(tenant_id, external_identity_subject_id)` | Yes (proposed) | optional active-only predicate by policy | Resolve subject membership within tenant | Tenant-scoped authorization lookup; uniqueness prevents duplicate memberships (exact temporal/status semantics may refine predicate). |
| `core.tenant_membership` | `ix_tenant_membership_subject` | `(external_identity_subject_id, tenant_id)` | No | none | List memberships for principal | Cross-tenant listing only via controlled/admin paths; still useful for principal-centric resolution. |
| `core.role` | `pk_role` | `(role_id)` | Yes | none | Role lookup | PK. |
| `core.role` | `uq_role_scope_code` | `(COALESCE(tenant_id, '00000000-0000-0000-0000-000000000000'::uuid), role_code)` or equivalent partial uniques | Yes (proposed) | split global/tenant uniques as preferred | Resolve role by code/scope | Exact implementation (NULL handling) to be chosen; ensures deterministic role identity. |
| `core.role_permission` | `pk_role_permission` | `(role_permission_id)` | Yes | none | Row lookup | PK. |
| `core.role_permission` | `uq_role_permission_mapping` | `(role_id, permission_code, COALESCE(resource_scope,''))` | Yes | none | Permission evaluation | Canonical mapping uniqueness. |
| `core.role_permission` | `ix_role_permission_role` | `(role_id)` | No | none | Load permissions for role | Authorization checks. |
| `core.membership_role_assignment` | `pk_membership_role_assignment` | `(membership_role_assignment_id)` | Yes | none | PK |  |
| `core.membership_role_assignment` | `uq_membership_role_assignment` | `(tenant_membership_id, role_id)` | Yes (proposed) | optional active/effective predicate | Prevent duplicate assignment | May be refined for temporal assignments. |
| `core.membership_role_assignment` | `ix_membership_role_assignment_tenant_membership` | `(tenant_id, tenant_membership_id, assignment_status)` | No | none | Resolve effective roles for membership | Tenant-scoped auth path. |
| `core.support_access_grant` | `pk_support_access_grant` | `(support_access_grant_id)` | Yes | none | PK |  |
| `core.support_access_grant` | `ix_support_access_grant_target_status_expiry` | `(target_tenant_id, grant_status, expires_at)` | No | none | Find active/valid grants for tenant | JIT access validation. |
| `core.support_access_grant` | `ix_support_access_grant_grantee` | `(grantee_subject_id, grant_status, expires_at)` | No | none | Grants for principal | Support workflow. |
| `core.support_access_approval` | `pk_support_access_approval` | `(support_access_approval_id)` | Yes | none | PK |  |
| `core.support_access_approval` | `ix_support_access_approval_grant` | `(support_access_grant_id, decision)` | No | none | Approval state lookup | Workflow. |
| `core.tenant_configuration` | `pk_tenant_configuration` | `(tenant_configuration_id)` | Yes | none | PK |  |
| `core.tenant_configuration` | `uq_tenant_configuration_version` | `(tenant_id, config_domain, config_version)` | Yes | none | Versioned config identity | Prevents version collisions. |
| `core.tenant_configuration` | `ix_tenant_configuration_effective` | `(tenant_id, config_domain, config_status, effective_from DESC)` | No | none | Resolve effective config | Common read path. |
| `core.asset` | `pk_asset` | `(asset_id)` | Yes | none | Canonical asset lookup | PK. |
| `core.asset` | `uq_asset_tenant_asset` | `(tenant_id, asset_id)` | Yes | none | Tenant-consistent FK target | Enables composite tenant-safe references. |
| `core.asset` | `ix_asset_tenant_status_last_seen` | `(tenant_id, asset_status, last_seen_at DESC)` | No | none | Inventory/dashboard/status queries | Supports tenant asset views and operations. |
| `integration_ai.data_source` | `pk_data_source` | `(data_source_id)` | Yes | none | PK |  |
| `integration_ai.data_source` | `uq_data_source_tenant` | `(tenant_id, data_source_id)` | Yes | none | Tenant-consistent FK target | Composite FK support. |
| `integration_ai.data_source` | `ix_data_source_tenant_external` | `(tenant_id, external_source_identifier)` | Yes (proposed) | `WHERE external_source_identifier IS NOT NULL` | Source resolution | Connector/source lookup. |
| `core.asset_data_source` | `pk_asset_data_source` | `(asset_data_source_id)` | Yes | none | PK |  |
| `core.asset_data_source` | `uq_asset_data_source_tenant_binding` | `(tenant_id, asset_data_source_id)` | Yes | none | Tenant-consistent FK target | Composite FK support. |
| `core.asset_data_source` | `uq_asset_data_source_source_device_key` | `(tenant_id, source_device_key_id)` | Yes | none | **Authoritative stable binding key uniqueness (Proposed, OD-002)** | Prevents competing binding identities; supports deterministic resolution. |
| `core.asset_data_source` | `ix_asset_data_source_tenant_asset` | `(tenant_id, asset_id, binding_status)` | No | none | Bindings for canonical asset | Licensing/identity/history queries. |
| `core.asset_data_source` | `ix_asset_data_source_tenant_source` | `(tenant_id, data_source_id, binding_status)` | No | none | Bindings reported by source | Ingestion/connector resolution. |
| `core.source_device_key` | `pk_source_device_key` | `(source_device_key_id)` | Yes | none | Dependent projection lookup | 1:1 with authoritative binding key. |
| `core.source_device_key` | `uq_source_device_key_binding` | `(asset_data_source_id)` | Yes | none | 1:1 binding projection | Prevents competing rows. |
| `core.source_device_fingerprint_alias` | `pk_source_device_fingerprint_alias` | `(source_device_fingerprint_alias_id)` | Yes | none | PK |  |
| `core.source_device_fingerprint_alias` | `ix_fingerprint_alias_lookup` | `(tenant_id, fingerprint_algorithm, fingerprint_value_protected, alias_status)` | Proposed unique/partial | active/effective predicate TBD (OD-006/overlap semantics) | Resolve fingerprint to stable binding identity | Critical identity-resolution path; exact uniqueness must respect approved overlap/rotation rules. |
| `core.source_device_fingerprint_alias` | `ix_fingerprint_alias_binding` | `(tenant_id, asset_data_source_id, effective_from DESC)` | No | none | Alias history for binding | Rotation/audit/provenance. |
| `core.asset_identity_claim` | `pk_asset_identity_claim` | `(asset_identity_claim_id)` | Yes | none | PK |  |
| `core.asset_identity_claim` | `ix_asset_identity_claim_resolution` | `(tenant_id, identity_resolution_case_id, claim_status)` | No | none | Claims in resolution case | Workflow. |
| `core.asset_identity_claim` | `ix_asset_identity_claim_source_ref` | `(tenant_id, data_source_id, source_claim_reference)` | Proposed unique | `WHERE source_claim_reference IS NOT NULL` | Source claim dedupe/correlation | If source provides stable refs. |
| `core.identity_resolution_case` | `pk_identity_resolution_case` | `(identity_resolution_case_id)` | Yes | none | PK |  |
| `core.identity_resolution_case` | `ix_identity_resolution_case_tenant_status` | `(tenant_id, case_status, opened_at DESC)` | No | none | Pending/conflict case queue | Operational resolution. |
| `core.asset_lifecycle_event` | `pk_asset_lifecycle_event` | `(asset_lifecycle_event_id)` | Yes | none | PK |  |
| `core.asset_lifecycle_event` | `ix_asset_lifecycle_event_asset_time` | `(tenant_id, asset_id, occurred_at DESC)` | No | none | Asset history timeline | Audit/investigation. |
| `core.asset_merge_operation` | `pk_asset_merge_operation` | `(asset_merge_operation_id)` | Yes | none | PK |  |
| `core.asset_merge_operation` | `ix_asset_merge_operation_tenant_status` | `(tenant_id, operation_status, requested_at DESC)` | No | none | Operation tracking | Workflow/audit. |
| `core.asset_split_operation` | `pk_asset_split_operation` | `(asset_split_operation_id)` | Yes | none | PK |  |
| `core.asset_split_operation` | `ix_asset_split_operation_tenant_status` | `(tenant_id, operation_status, requested_at DESC)` | No | none | Operation tracking | Workflow/audit. |
| `core.asset_lineage_link` | `pk_asset_lineage_link` | `(asset_lineage_link_id)` | Yes | none | PK |  |
| `core.asset_lineage_link` | `ix_asset_lineage_link_from` | `(tenant_id, from_asset_id, effective_at DESC)` | No | none | Lineage traversal | History queries. |
| `core.asset_lineage_link` | `ix_asset_lineage_link_to` | `(tenant_id, to_asset_id, effective_at DESC)` | No | none | Reverse lineage traversal | Investigation. |
| `core.asset_lineage_link` | `uq_asset_lineage_link_edge` | `(tenant_id, link_type, from_asset_id, to_asset_id, COALESCE(merge_operation_id,'00000000-0000-0000-0000-000000000000'::uuid), COALESCE(split_operation_id,'00000000-0000-0000-0000-000000000000'::uuid))` (proposed form) | Yes (proposed) | none | Prevent duplicate lineage edges | Exact expression/columns to be finalized; enforces integrity. |
| `core.subscription_entitlement` | `pk_subscription_entitlement` | `(subscription_entitlement_id)` | Yes | none | PK |  |
| `core.subscription_entitlement` | `ix_subscription_entitlement_tenant_effective` | `(tenant_id, entitlement_status, effective_from DESC)` | No | none | Resolve active entitlement | Licensing checks. |
| `core.tenant_license_usage_state` | `pk_tenant_license_usage_state` | `(tenant_license_usage_state_id)` | Yes | none | PK |  |
| `core.tenant_license_usage_state` | `uq_tenant_license_usage_scope` | `(tenant_id, usage_scope)` | Yes | none | One state row per scope | Atomic update target. |
| `core.asset_license_event` | `pk_asset_license_event` | `(asset_license_event_id)` | Yes | none | PK |  |
| `core.asset_license_event` | `ix_asset_license_event_tenant_time` | `(tenant_id, occurred_at DESC)` | No | none | License history / reconciliation | Time-based audit. |
| `core.asset_license_event` | `ix_asset_license_event_asset` | `(tenant_id, asset_id, occurred_at DESC)` | No | `WHERE asset_id IS NOT NULL` | Asset licensing history | Investigation. |
| `core.identity_operation_idempotency_ledger` | `pk_identity_operation_idempotency_ledger` | `(identity_operation_idempotency_ledger_id)` | Yes | none | PK |  |
| `core.identity_operation_idempotency_ledger` | `uq_identity_idempotency_scope` | `(tenant_id, operation_type, idempotency_key)` | Yes | none | **Required idempotency uniqueness (OD-008)** | Prevents duplicate identity/licensing effects under retries/concurrency. |
| `core.identity_operation_idempotency_ledger` | `ix_identity_idempotency_state` | `(tenant_id, request_state, last_attempt_at DESC)` | No | partial for `in_progress`/`timeout_unknown_commit` proposed | Recovery/reconciliation scans | Supports timeout/unknown-commit processing. |
| `core.asset_license_reservation` | `pk_asset_license_reservation` | `(asset_license_reservation_id)` | Yes | none | PK |  |
| `core.asset_license_reservation` | `ix_asset_license_reservation_tenant_status` | `(tenant_id, reservation_status, expires_at)` | No | none | Active/expiring reservations | Enforcement/release flows (OD-003). |
| `core.asset_tombstone` | `pk_asset_tombstone` | `(asset_tombstone_id)` | Yes | none | PK |  |
| `core.asset_tombstone` | `uq_asset_tombstone_asset` | `(tenant_id, asset_id)` | Yes | none | One tombstone per terminal asset | Prevents duplicate terminal records. |
| `ingest.event_schema_reference` | `pk_event_schema_reference` | `(event_schema_reference_id)` | Yes | none | PK |  |
| `ingest.event_schema_reference` | `uq_event_schema_ref` | `(schema_namespace, schema_name, schema_version)` | Yes | none | Schema resolution | Validation/normalization. |
| `ingest.event_receipt` | `pk_event_receipt` | `(event_receipt_id)` | Yes | none | PK |  |
| `ingest.event_receipt` | `uq_event_receipt_dedup_device_scoped` | `(tenant_id, data_source_id, source_device_key_id, event_namespace, upstream_event_identifier)` | Yes (proposed) | `WHERE upstream_event_identifier IS NOT NULL AND source_device_key_id IS NOT NULL` | **Device-scoped event dedup (OD-013)** | Prevents cross-device collisions in multi-device connectors; exact namespace predicate per approved semantics. |
| `ingest.event_receipt` | `uq_event_receipt_dedup_fallback` | `(tenant_id, data_source_id, event_namespace, fallback_dedup_fingerprint)` | Yes (proposed) | `WHERE fallback_dedup_fingerprint IS NOT NULL` | Fallback dedup when upstream ID missing/unreliable | Connector-specific policy-dependent; must be explicit. |
| `ingest.event_receipt` | `ix_event_receipt_tenant_received` | `(tenant_id, received_at DESC)` | No | none | Recent ingestion / time-based queries | Operational dashboard/support; partitioning may later change local index shape. |
| `ingest.event_receipt` | `ix_event_receipt_asset_time` | `(tenant_id, asset_id, event_time DESC)` | No | `WHERE asset_id IS NOT NULL` | Asset event timeline | Investigation/correlation. |
| `ingest.security_event` | `pk_security_event` | `(security_event_id)` | Yes | none | PK |  |
| `ingest.security_event` | `uq_security_event_receipt` | `(tenant_id, event_receipt_id)` | Yes (proposed if 1:1) | none | One normalized event per receipt | Integrity/correlation. |
| `ingest.security_event` | `ix_security_event_tenant_time` | `(tenant_id, event_time DESC)` | No | none | Time-based security queries | Dashboard/investigation; partition candidate. |
| `ingest.security_event` | `ix_security_event_tenant_asset_time` | `(tenant_id, asset_id, event_time DESC)` | No | `WHERE asset_id IS NOT NULL` | Asset-centric security timeline | Common SOC query. |
| `processing.outbox_message` | `pk_outbox_message` | `(outbox_message_id)` | Yes | none | PK |  |
| `processing.outbox_message` | `ix_outbox_message_claimable` | `(message_status, available_at, created_at)` | No | `WHERE message_status IN ('pending','retryable')` (proposed) | Claim/dispatch queue | Supports leasing/claim scans; exact status set depends on state machine. |
| `processing.outbox_message` | `uq_outbox_message_dedupe` | `(tenant_id, dedupe_key)` | Yes (proposed) | `WHERE dedupe_key IS NOT NULL` | Idempotent enqueue | Prevents duplicate work intents when used. |
| `processing.outbox_message` | `ix_outbox_message_tenant_status` | `(tenant_id, message_status, available_at)` | No | tenant-scoped predicate as needed | Tenant-scoped operational views | Admin/support queries. |
| `processing.outbox_attempt` | `pk_outbox_attempt` | `(outbox_attempt_id)` | Yes | none | PK |  |
| `processing.outbox_attempt` | `uq_outbox_attempt_number` | `(outbox_message_id, attempt_number)` | Yes | none | Attempt ordering/integrity | Recovery/audit. |
| `processing.outbox_attempt` | `ix_outbox_attempt_lease` | `(attempt_status, lease_expires_at)` | No | active/unknown predicates proposed | Lease expiry/reaper/unknown-outcome scans | Operational reliability (OD-009). |
| `processing.processing_work_item` | `pk_processing_work_item` | `(processing_work_item_id)` | Yes | none | PK | Optional table. |
| `processing.processing_work_item` | `ix_processing_work_item_claimable` | `(work_status, available_at)` | No | pending/eligible predicate | Optional claim queue | Only if table used. |
| `audit_evidence.audit_event` | `pk_audit_event` | `(audit_event_id)` | Yes | none | PK |  |
| `audit_evidence.audit_event` | `ix_audit_event_tenant_time` | `(tenant_id, occurred_at DESC)` | No | none | Tenant audit timeline | Compliance/investigation. |
| `audit_evidence.audit_event` | `ix_audit_event_target` | `(tenant_id, target_entity_type, target_entity_id, occurred_at DESC)` | No | none | Entity-focused audit lookup | Traceability. |
| `audit_evidence.audit_event` | `ix_audit_event_correlation` | `(correlation_id)` | No | `WHERE correlation_id IS NOT NULL` | Cross-record correlation | Support/debug (bounded). |
| `audit_evidence.forensic_evidence_record` | `pk_forensic_evidence_record` | `(forensic_evidence_record_id)` | Yes | none | PK |  |
| `audit_evidence.forensic_evidence_record` | `ix_forensic_evidence_tenant_status` | `(tenant_id, evidence_status, collected_at DESC)` | No | none | Evidence inventory | Case management. |
| `audit_evidence.evidence_object_version` | `pk_evidence_object_version` | `(evidence_object_version_id)` | Yes | none | PK |  |
| `audit_evidence.evidence_object_version` | `uq_evidence_object_version` | `(forensic_evidence_record_id, version_number)` | Yes | none | Immutable version identity | Integrity. |
| `audit_evidence.evidence_custody_event` | `pk_evidence_custody_event` | `(evidence_custody_event_id)` | Yes | none | PK |  |
| `audit_evidence.evidence_custody_event` | `ix_evidence_custody_record_time` | `(tenant_id, forensic_evidence_record_id, occurred_at DESC)` | No | none | Chain-of-custody timeline | Forensic traceability. |
| `audit_evidence.evidence_transition_authorization` | `pk_evidence_transition_authorization` | `(evidence_transition_authorization_id)` | Yes | none | PK |  |
| `audit_evidence.evidence_transition_authorization` | `ix_evidence_transition_record` | `(tenant_id, forensic_evidence_record_id, authorization_status)` | No | none | Controlled transition checks | Governance. |
| `audit_evidence.ai_interaction_audit` | `pk_ai_interaction_audit` | `(ai_interaction_audit_id)` | Yes | none | PK |  |
| `audit_evidence.ai_interaction_audit` | `ix_ai_interaction_audit_tenant_time` | `(tenant_id, occurred_at DESC)` | No | none | AI audit timeline | Compliance/privacy review. |
| `audit_evidence.ai_interaction_audit` | `ix_ai_interaction_audit_provider` | `(tenant_id, provider_configuration_id, occurred_at DESC)` | No | `WHERE provider_configuration_id IS NOT NULL` | Provider-specific audit | Governance. |
| `integration_ai.integration_configuration` | `pk_integration_configuration` | `(integration_configuration_id)` | Yes | none | PK |  |
| `integration_ai.integration_configuration` | `ix_integration_configuration_tenant_code` | `(tenant_id, integration_code, configuration_status)` | No | none | Resolve integration config | Admin/runtime lookup. |
| `integration_ai.tenant_ai_provider_configuration` | `pk_tenant_ai_provider_configuration` | `(tenant_ai_provider_configuration_id)` | Yes | none | PK |  |
| `integration_ai.tenant_ai_provider_configuration` | `ix_tenant_ai_provider_tenant_effective` | `(tenant_id, configuration_status, is_default, effective_from DESC)` | No | none | Resolve explicit provider selection | No silent failover path. |
| `integration_ai.ai_provider_secret_reference` | `pk_ai_provider_secret_reference` | `(ai_provider_secret_reference_id)` | Yes | none | PK |  |
| `integration_ai.ai_provider_secret_reference` | `uq_ai_provider_secret_purpose` | `(tenant_id, provider_configuration_id, secret_purpose)` | Yes (proposed) | none | Secret reference identity | Rotation governance. |
| `integration_ai.ai_provider_policy_consent_reference` | `pk_ai_provider_policy_consent_reference` | `(ai_provider_policy_consent_reference_id)` | Yes | none | PK |  |
| `integration_ai.ai_provider_policy_consent_reference` | `ix_ai_policy_consent_tenant_effective` | `(tenant_id, provider_configuration_id, policy_type, consent_status, effective_from DESC)` | No | none | Consent/policy checks | Data governance. |
| `integration_ai.ai_usage_budget_accounting` | `pk_ai_usage_budget_accounting` | `(ai_usage_budget_accounting_id)` | Yes | none | PK |  |
| `integration_ai.ai_usage_budget_accounting` | `uq_ai_usage_budget_period` | `(tenant_id, provider_configuration_id, accounting_period_start)` | Proposed | policy-dependent | Period accounting identity | Prevent duplicate period rows if modeled that way. |
| `soc.alert` | `pk_alert` | `(alert_id)` | Yes | none | PK |  |
| `soc.alert` | `ix_alert_tenant_status_time` | `(tenant_id, alert_status, detected_at DESC)` | No | none | Alert queue/dashboard | SOC operations. |
| `soc.alert` | `ix_alert_asset_time` | `(tenant_id, asset_id, detected_at DESC)` | No | `WHERE asset_id IS NOT NULL` | Asset alert history | Investigation. |
| `soc.incident_case` | `pk_incident_case` | `(incident_case_id)` | Yes | none | PK |  |
| `soc.incident_case` | `ix_incident_case_tenant_status` | `(tenant_id, case_status, opened_at DESC)` | No | none | Case queue | SOC operations. |
| `soc.detection_rule` | `pk_detection_rule` | `(detection_rule_id)` | Yes | none | PK |  |
| `soc.detection_rule_version` | `pk_detection_rule_version` | `(detection_rule_version_id)` | Yes | none | PK |  |
| `soc.detection_rule_version` | `uq_detection_rule_version` | `(detection_rule_id, version_number)` | Yes | none | Version identity | Immutable rule snapshots. |
| `soc.vulnerability_finding` | `pk_vulnerability_finding` | `(vulnerability_finding_id)` | Yes | none | PK |  |
| `soc.vulnerability_finding` | `ix_vulnerability_finding_tenant_status` | `(tenant_id, finding_status, detected_at DESC)` | No | none | Findings dashboard | Remediation tracking. |
| `soc.vulnerability_finding` | `ix_vulnerability_finding_asset` | `(tenant_id, asset_id, detected_at DESC)` | No | `WHERE asset_id IS NOT NULL` | Asset findings | Investigation. |
| `soc.threat_intelligence_reference` | `pk_threat_intelligence_reference` | `(threat_intelligence_reference_id)` | Yes | none | PK | Global catalog. |
| `soc.threat_intelligence_reference` | `uq_threat_intel_source_ref` | `(source_name, external_reference)` | Yes | none | Catalog identity | Dedup/reference. |
| `soc.asset_inventory_observation` | `pk_asset_inventory_observation` | `(asset_inventory_observation_id)` | Yes | none | PK |  |
| `soc.asset_inventory_observation` | `ix_inventory_observation_asset_time` | `(tenant_id, asset_id, observed_at DESC)` | No | `WHERE asset_id IS NOT NULL` | Asset inventory timeline | Common query; time-series growth. |
| `soc.asset_inventory_observation` | `ix_inventory_observation_tenant_time` | `(tenant_id, observed_at DESC)` | No | none | Recent observations | Operational/retention jobs. |

## 3. Required pattern coverage

- **Identity resolution and binding lookups:** `core.asset_data_source` unique `(tenant_id, source_device_key_id)`; tenant/source/asset lookup indexes; `core.source_device_fingerprint_alias` lookup/history indexes; identity claim/case indexes.
- **Event deduplication:** explicit namespace-aware unique indexes on `ingest.event_receipt` (device-scoped upstream ID and fallback fingerprint), plus tenant/time/asset access indexes.
- **Idempotency ledger:** unique `(tenant_id, operation_type, idempotency_key)` and recovery-state scan index on `core.identity_operation_idempotency_ledger`.
- **Audit and evidence retrieval:** tenant/time/target/correlation indexes for `audit_evidence.audit_event`; status/time/version/custody/transition indexes for evidence tables; AI interaction audit timeline/provider indexes.
- **Time-based and dashboard queries:** descending time indexes on lifecycle/license/receipt/security/audit/alerts/incidents/findings/observations as listed.
- **Outbox claiming:** partial claimable index and dedupe unique on `processing.outbox_message`; attempt ordering and lease/unknown-state scan indexes on `processing.outbox_attempt`.

## 4. Trade-offs and validation needs

- Each additional index increases INSERT/UPDATE/DELETE cost, WAL volume, storage, and vacuum/autovacuum work; high-churn tables (`ingest.event_receipt`, `ingest.security_event`, `processing.outbox_*`, `audit_evidence.audit_event`, observations) require careful validation.
- Partial indexes reduce size but require predicates to match query shapes; exact status/state vocabularies must be finalized.
- JSONB GIN indexes are **not proposed by default**; add only for proven query paths with selectivity and sensitivity review.
- Workload/query-plan validation, index bloat monitoring, and periodic review are required before implementation (see lifecycle/operations document).
