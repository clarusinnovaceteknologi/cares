# CARES PostgreSQL Logical Model Round 1.1 — Final Audit & Publication Correction

**Status:** Audit and publication-correction report (documentation only); **NOT IMPLEMENTED, NOT TESTED**. This report does not create PostgreSQL DDL, migrations, database objects, policies, roles, application code, or tests. No ADR status is changed (**ADR 0006 remains Proposed**). No owner/finance/privacy/legal/security approvals are invented.

**Audit date (local):** 2026-11-22 (execution context)
**Repository (publication target):** https://github.com/clarusinnovaceteknologi/cares
**Publication branch:** `audit/postgresql-round1-1-publication`
**Initial publication commit inspected:** `888905d8aef8bf6eb2e874cf9804a239f0f6f51a`

## Executive summary

A focused independent audit was performed on the PostgreSQL Logical Model Round 1.1 documentation artifacts (local workspace sources/exports and published audit package context on the publication branch). The five principal technical areas (A–E) are **substantially consistent and corrected in intent** across the logical model, ERDs, transaction boundaries, open decisions, and Round 1.1 changelog: binding ownership is clearly recommended as `asset_data_source` authoritative with dependent non-authoritative `source_device_key` projection only if materialized (OD-002 open); identity/licensing idempotency contract and A/B coupling are explicitly documented without claiming exactly-once external delivery (OD-008 open); event receipt deduplication uses explicit namespace/provenance with device-scoped collision prevention guidance and OD-013 for connector-specific fallback behavior; merge/split lineage is modeled with typed relational references (no polymorphic `from_asset_or_op_ref` attribute in current model/ERD definitions); and entity naming/responsibility boundaries are distinguished in intent.

**Cross-document/catalogue issues found:** the logical data model catalogue contained multiple duplicate/misplaced entity rows introduced in prior edits, creating a clear internal documentation inconsistency despite correct Round 1.1 semantics being present. A **narrowly scoped correction** was applied in this audit pass to deduplicate catalogue rows in `docs/POSTGRESQL_LOGICAL_DATA_MODEL.md` (documented below) without changing technical design intent. The published external audit README was **stale** relative to actual GitHub publication state and has been corrected to reflect repository/branch/commit and file locations while preserving historical packaging facts.

**Mermaid validation:** 4 `erDiagram` blocks and 40 unique entity definitions were structurally identified in `docs/POSTGRESQL_LOGICAL_ERD.md`; no Mermaid renderer/parser CLI (`mmdc`, `npx` mermaid tooling) was available, so **visual rendering was not performed** and structural checks must not be reported as visual validation.

**Open decisions:** OD-001–OD-013 remain open/proposed as documented (no statuses changed). OD-002 and OD-008 require formal technical approval and block targeted physical identity/licensing/idempotency schema decisions; OD-003/OD-004 and parts of OD-001 block licensing accounting enforcement semantics; OD-013 partially blocks supported-connector event dedup uniqueness/fallback design. Other ODs block or bound specific physical/governance details rather than the entire Round 2 logical design effort.

**Final recommendation:** **READY FOR ROUND 2 WITH EXPLICITLY BOUNDED EXCLUSIONS** (design/planning only, subject to exclusions and approvals below). This does **not** authorize physical schema implementation.

## Documents actually inspected

### Published audit package and publication artifacts (local copies; remote publication context verified)
| Artifact | Path / location | Inspection performed |
|---|---|---|
| External audit README (published/stale state and corrected local copy) | `dist/cares-external-audit/README.md`; remote blob on `audit/postgresql-round1-1-publication` (commit `888905d...`) retrieved via GitHub repository tools | Full text reviewed; staleness and provenance claims assessed; local correction applied |
| Round 1.1 execution report (packaged) | `dist/cares-external-audit/copilot.txt`; remote blob on `audit/postgresql-round1-1-publication` retrieved | Full text reviewed (baseline, changes, findings, validations, limitations, status claims) |
| Documentation ZIP | `dist/cares-external-audit/CARES_DOCUMENTATION_HTML.zip` (local) | SHA-256/hash comparison, `zipfile` integrity test, entry count, presence of index/manifest and 5 required principal HTML docs verified. **Remote ZIP binary contents not byte-inspected/download-verified in this environment** (limitation). |

### Local source and export artifacts (Round 1.1 deliverables in workspace)
| Artifact | Path | Inspection performed |
|---|---|---|
| Logical data model (Markdown source) | `docs/POSTGRESQL_LOGICAL_DATA_MODEL.md` | Full structural review with targeted reads/searches: binding, idempotency, event receipt, lineage, merge/split, naming-boundary entities, Round 1.1 sections, catalogue/relationship context, duplicate-row consistency |
| Logical ERD (Markdown source) | `docs/POSTGRESQL_LOGICAL_ERD.md` | Full review: conventions, 4 Mermaid `erDiagram` blocks, entity definitions, relationships, explanations, omitted/simplified entities, assumptions/limitations; searched for obsolete `from_asset_or_op_ref` attribute |
| Transaction boundaries (Markdown source) | `docs/POSTGRESQL_TRANSACTION_BOUNDARIES.md` | Full/targeted review: global constraints, operations 1–13, idempotency taxonomy, event ingestion/outbox/unknown delivery, Round 1.1 consistency notes |
| Open decisions (Markdown source) | `docs/POSTGRESQL_SCHEMA_OPEN_DECISIONS.md` | Full review: OD-001–OD-013 register, blockers/approvals, resolution order, readiness assessment, Round 1.1 correction notes |
| Round 1.1 changelog (Markdown source) | `docs/POSTGRESQL_LOGICAL_MODEL_ROUND1_1_CHANGELOG.md` | Full review: scope, findings/corrections, alternatives/recommendations, documents changed/not changed, confirmations |
| Export index/manifest | `dist/cares-documentation-html/index.html`, `dist/cares-documentation-html/EXPORT_MANIFEST.json` | Presence and manifest metadata/coverage/failures/link/asset fields inspected |
| Principal HTML exports (local) | `dist/cares-documentation-html/docs/POSTGRESQL_LOGICAL_DATA_MODEL.md.html`, `.../POSTGRESQL_LOGICAL_ERD.md.html`, `.../POSTGRESQL_TRANSACTION_BOUNDARIES.md.html`, `.../POSTGRESQL_SCHEMA_OPEN_DECISIONS.md.html`, `.../POSTGRESQL_LOGICAL_MODEL_ROUND1_1_CHANGELOG.md.html` | Presence confirmed in export directory and ZIP; selected content parity signals (titles/sections present) and index/manifest inclusion verified |
| Root execution report | `copilot.txt` | Reviewed and updated in this audit correction pass |

### Supporting baseline documents inspected
| Artifact | Path | Inspection performed |
|---|---|---|
| Data architecture | `docs/DATA_ARCHITECTURE.md` | Targeted consistency reference (identity/licensing, outbox/idempotency, event receipt, tenant isolation concepts) |
| Security architecture | `docs/SECURITY_ARCHITECTURE.md` | Targeted consistency reference (tenant boundary, verified context, RLS defense-in-depth, AI/provider governance, audit separation concepts) |
| PostgreSQL technical decisions | `docs/POSTGRESQL_TECHNICAL_DECISIONS.md` | Targeted consistency reference (tenant context/RLS, outbox/idempotency, retention/operational concerns) |
| ADR 0003 | `docs/adr/0003-device-identity-and-asset-licensing.md` | Reviewed for identity/binding/asset/licensing constraints |
| ADR 0005 | `docs/adr/0005-event-processing-and-broker-evolution.md` | Reviewed for event receipt/outbox/idempotent processing constraints |
| ADR 0006 | `docs/adr/0006-atomic-per-tenant-asset-licensing.md` | Reviewed for proposed (not accepted) licensing semantics and schema-ambiguity context; **status confirmed Proposed** |

**Not inspected / limitations:** full visual Mermaid rendering (no renderer); remote GitHub ZIP binary download/byte comparison; complete line-by-line diff of every non-principal Markdown/HTML document beyond targeted consistency checks; runtime behavior, database state, or implementation artifacts (none exist/authorized).

## Technical audit findings

### A. Source-device binding and identity ownership
**Classification:** **PASS WITH LIMITATIONS**

| Check | Evidence (document/section/entity/relationship) | Result | Notes |
|---|---|---|---|
| `asset_data_source` consistently defined as authoritative stable binding (recommended) | `docs/POSTGRESQL_LOGICAL_DATA_MODEL.md` §3.2 `asset_data_source`, identity model notes, §9.1; `docs/POSTGRESQL_LOGICAL_ERD.md` conventions, ERD 1/2 entities/relations and explanation; `docs/POSTGRESQL_TRANSACTION_BOUNDARIES.md` global constraints, ops 1–2/6–7 and Round 1.1 notes; `docs/POSTGRESQL_SCHEMA_OPEN_DECISIONS.md` OD-002; `docs/POSTGRESQL_LOGICAL_MODEL_ROUND1_1_CHANGELOG.md` finding 1 | PASS (Proposed) | Recommendation explicit and consistent: `asset_data_source` owns stable binding identity/lifecycle/provenance. |
| `source_device_key_id` ownership and cardinality unambiguous in recommendation | Model: `asset_data_source` owns immutable `source_device_key_id`; `source_device_key` only 1:1 dependent/non-authoritative projection if materialized, same lifecycle, no competing attributes. ERD 1/2: `ASSET_DATA_SOURCE` has `source_device_key_id`; `SOURCE_DEVICE_KEY` shown as dependent 1:1 projection; relation labeled accordingly. Tx boundaries ops 1–2/6–7 preserve single authoritative binding identity. | PASS (Proposed) | OD-002 remains open/approval-required; cardinality/ownership is clearly recommended but **not approved**. |
| Aliases resolve to same stable binding identity | Model `source_device_fingerprint_alias` FK/reference to stable binding identity owned by `asset_data_source`; ERD 1/2 `SOURCE_DEVICE_FINGERPRINT_ALIAS` → `SOURCE_DEVICE_KEY`/stable binding identity context; tx ops 3–4/6–7 preserve same binding/asset resolution. | PASS (Proposed) | Overlap/versioning represented as proposed without raw-ID uniqueness keys. |
| Optional `source_device_key` projection cannot become competing identity authority | Model explicitly states non-authoritative dependent projection, 1:1, no competing lifecycle/identity attributes; ERD convention/relations consistent; changelog/OD-002 rationale consistent. | PASS (Proposed) | Depends on future approved/implemented physical constraints (not present). |
| ERD, logical model, and transaction documentation agree | Cross-checked entity names/relationships/ownership statements across principal docs and changelog/OD-002. | PASS WITH LIMITATIONS | Agreement is at proposed-logical level; formal technical approval and physical enforcement details remain open. |

**Remaining ambiguity:** formal approval/acceptance of Alternative A vs any alternative (OD-002), and whether a separate dependent `source_device_key` projection is materialized physically.

### B. Identity and licensing idempotency
**Classification:** **PASS WITH LIMITATIONS**

| Check | Evidence | Result | Notes |
|---|---|---|---|
| Idempotency scope and key uniqueness specified | Model `identity_operation_idempotency_ledger` and §9.2: `(tenant_id, operation_type, idempotency_key)` unique within approved scope; ERD 2 shows `operation_type`, `idempotency_key`, `request_hash`, `state`; Tx global constraints/op 1-2/5-9/notes; OD-008. | PASS (Proposed) | Covered operation set/retention window require approval. |
| Canonical request representation and hashing specified | Model §9.2 and entity definition: deterministic canonicalization and request hash/fingerprint; Tx/OD-008 consistent. | PASS (Proposed) | Exact canonicalization/hash standard not finalized (approval required). |
| Request state transitions specified | Model/ERD/Tx/OD-008: `in_progress`, `committed`, `failed_terminal`, `timeout_unknown_commit` (and replay/conflict handling described). | PASS (Proposed) | Terminal/reconciliation rules require approval. |
| Concurrent duplicate request handling specified | Model §9.2, Tx global constraints and ops (claim/serialize/recheck semantics), ERD ledger role. | PASS (Proposed) | Physical locking/fencing details deferred. |
| Replay and conflicting-payload behavior specified | Same key + same canonical request => committed/original outcome (or explicit in-progress/unknown state); same key + different request/hash => conflict/reject. | PASS (Proposed) | Consistent across principal docs. |
| Timeout and unknown-commit recovery specified | `timeout_unknown_commit` requires reconciliation against durable DB state; must not assume blind success/failure. | PASS (Proposed) | Workflow/SLA details open. |
| Retention and reconciliation specified as required | Model/OD-008/Tx notes require retention and reconciliation windows/workflow (approval needed). | PASS WITH LIMITATIONS | Specific retention/reconciliation policy not approved. |
| Transaction boundaries for DB-local identity/licensing operations specified | Tx boundaries define single-transaction atomicity for required business/idempotency/audit/outbox consistency per operation; Alternative A recommended default for DB-local ops, B only with leases/fencing/recovery and approval. | PASS (Proposed) | DB-local only; does not include external side effects. |
| No claim of exactly-once external delivery | Tx global constraints, op 12, cross-operation notes, changelog, OD-008/OD-009 context explicitly distinguish external side effects and unknown delivery outcomes. | PASS | Consistently stated. |

**Remaining ambiguity:** approval of operation scope, canonicalization/hash standard, final state machine/terminal rules, retention/reconciliation workflow, and any staged (B) exceptions (OD-008).

### C. Event receipt deduplication
**Classification:** **PASS WITH LIMITATIONS**

| Check | Evidence | Result | Notes |
|---|---|---|---|
| Event dedup uses correct namespace (distinct from identity/licensing ledger) | Model `event_receipt` and §9.3; ERD 1/3 fields `dedup_namespace_type_id`/explicit namespace and normalized source key; Tx op 10 and taxonomy; OD-013; changelog finding 3. Distinct from `identity_operation_idempotency_ledger`. | PASS (Proposed) | Explicitly separated mechanisms. |
| Device-scoped upstream event identifiers cannot collide across different devices | Model §9.3 and `event_receipt`: device-scoped IDs must use tenant + authoritative stable source-device binding identity namespace (`asset_data_source`/`source_device_key_id` context), not `data_source_id` alone. Tx op 10 states same. OD-013 records requirement. | PASS (Proposed) | Requires correct namespace derivation for supported connectors (approval/bounding needed). |
| Data-source-global identifiers handled consistently | Tenant + `data_source_id` namespace allowed when upstream ID globally unique within data source/connector instance. | PASS (Proposed) | Connector capability classification remains open (OD-013). |
| Missing or unreliable upstream identifiers have explicit handling policy direction | Deterministic approved fallback strategy or reject/quarantine per approved connector policy; connector-specific behavior Open Decision. | PASS WITH LIMITATIONS | Policy/fallback not finalized (OD-013). |
| Connector-specific fallback behavior correctly represented by OD-013 | `docs/POSTGRESQL_SCHEMA_OPEN_DECISIONS.md` OD-013 added/refined with partial/open status and physical/connector blocker notes. | PASS | OD-013 remains open. |
| Compatible terminology and key semantics across related documents | `event_receipt`, namespace type/id, normalized source event key, provenance/device-scope context, no raw source IDs as DB uniqueness keys used consistently in model/ERD/Tx/OD/changelog. | PASS WITH LIMITATIONS | Physical uniqueness constraint details and pre-binding edge-case namespace derivation require approval/bounding. |

**Remaining ambiguity:** connector capability classification, approved deterministic fallback/reject/quarantine behavior for unreliable/missing IDs, payload-hash conflict policy details, and namespace derivation for pre-binding/unresolved identity cases (OD-013).

### D. Asset lineage and relational integrity
**Classification:** **PASS**

| Check | Evidence | Result | Notes |
|---|---|---|---|
| Previous polymorphic `from_asset_or_op_ref` design removed from current definitions | Model catalogue `asset_lineage_link` and §9.4 define typed FKs (`from_asset_id`, `to_asset_id`, nullable `merge_operation_id`, `split_operation_id` by link type); ERD 2 shows typed attributes/relationships; Tx ops 6–7 and notes require typed relational references. `grep` found **no `from_asset_or_op_ref` attribute in ERD**; mentions in model/tx/OD/changelog are historical correction context ("replaced... no generic polymorphic..."). | PASS | Correction is documented as proposed logical replacement. |
| Typed asset references used | `from_asset_id` and `to_asset_id` FKs to `asset` in model/ERD/Tx. | PASS | — |
| Merge and split operation references have appropriate relational semantics | Typed nullable `merge_operation_id` / `split_operation_id` with link-type/exclusivity intent; `ASSET_MERGE_OPERATION` / `ASSET_SPLIT_OPERATION` related to `ASSET_LINEAGE_LINK` in ERD 2; ops 6–7 persist operation records and typed lineage links. | PASS (Proposed logical) | Physical check-constraint syntax/enforcement deferred to future schema design. |
| Documented relationship types and FK expectations internally consistent | Model relationship analysis/matrices, ERD 2 relations, tx ops 6–7 consistent on typed lineage and preserved canonical IDs/non-reuse/tenant boundaries. | PASS | — |
| No ERD or catalogue section retains obsolete polymorphic references as current design | Current ERD entity/relationship definitions use typed lineage; catalogue defines typed `asset_lineage_link`. Residual term appears only in explanatory/historical correction text. | PASS | — |

### E. Entity naming and responsibility boundaries
**Classification:** **PASS WITH LIMITATIONS**

| Check | Evidence | Result | Notes |
|---|---|---|---|
| `role_permission` vs `membership_role_assignment` distinguished | Model 3.1 defines `role_permission` as canonical role→capability mapping and `membership_role_assignment` as membership→role (separate responsibilities); ERD 4 includes `ROLE`, `ROLE_PERMISSION`, `MEMBERSHIP_ROLE_ASSIGNMENT`; §9.5 normalization comparison present. | PASS (Proposed) | Narrow catalogue deduplication applied in this audit to remove a duplicate `role_permission` row (see corrections). |
| `tenant_configuration` vs tenant policy references distinguished | `tenant_configuration` canonical (includes policy/version references, no competing `tenant_policy_reference` entity) in model 3.1/§9.5; ERD 4 shows `TENANT_CONFIGURATION`. | PASS (Proposed) | Narrow catalogue deduplication removed duplicate/misplaced `tenant_configuration` and redundant 3.7 repeats. |
| `ai_interaction_audit` vs `audit_event` distinguished | Model 3.5/3.6 and §9.5 retain separate specialized AI governance record correlated/cross-referenced with `audit_event` (no full prompt/response by default); ERD omissions note lists `AI_INTERACTION_AUDIT` as distinct/correlatable. | PASS (Proposed) | ERD simplifies AI audit detail (intentional omission documented). |
| `asset_tombstone` vs terminal asset lifecycle state distinguished | Model 3.2/3.7 context and §9.5 retain both concepts (terminal lifecycle state/history vs optional distinct tombstone historical representation); ERD 2 includes `ASSET_TOMBSTONE`. | PASS (Proposed) | Representation choice remains open/proposed. |
| `processing_work_item` vs core processing entities distinguished | Model marks `processing_work_item` optional/intentionally not core and not a competing source of truth with `event_receipt`/`outbox_message`; ERD omission notes list it as intentionally not core. | PASS (Proposed) | Appropriately bounded as optional. |
| `outbox_message` vs `outbox_attempt` distinguished | Model 3.4 and ERD 1/3 define both separately (message intent/state vs attempt/lease/fence/ambiguity/replay history); Tx ops 11–12 use both concepts. | PASS (Proposed) | Narrow catalogue deduplication removed duplicate `outbox_attempt` row. |
| Duplicate responsibilities / inconsistent names / missing catalogue entries / unexplained ERD omissions | Principal semantics consistent with Round 1.1 intent; however catalogue contained duplicate/misplaced rows (inconsistency). ERD omissions are explicitly documented in ERD and model §9.6. | **NEEDS CORRECTION (resolved in this audit pass)** | Essential narrow deduplication applied to `docs/POSTGRESQL_LOGICAL_DATA_MODEL.md`; ERD/tx/OD not changed for this issue. |

## Cross-document consistency audit

**Overall classification:** **PASS WITH LIMITATIONS** (after narrowly scoped catalogue deduplication correction)

| Area | Evidence compared | Result | Notes |
|---|---|---|---|
| Entity names and definitions | Logical model, ERD entity labels/attributes, tx/OD/changelog terminology | PASS WITH LIMITATIONS | Core Round 1.1 entities consistent in meaning; catalogue previously had duplicate rows (corrected). Case style differs between ERD (`UPPER_CASE`) and model (`snake_case`) but mappings are clear. |
| Relationship cardinality and optionality | ERD 1–4 relations, model relationship analysis, tx record groups | PASS (Proposed logical) | Physical cardinality enforcement deferred. |
| Primary identity ownership | Binding/key/alias relationships in model/ERD/tx/OD-002 | PASS (Proposed) | Consistent recommended ownership. |
| Transaction boundaries | 13 operations in `docs/POSTGRESQL_TRANSACTION_BOUNDARIES.md` vs idempotency/event/outbox/lineage model and OD-008/OD-009/OD-013 | PASS WITH LIMITATIONS | Boundaries are proposed/logical; 13 operations present and aligned with corrected concepts. |
| Idempotency semantics | Ledger contract in model/§9.2, ERD 2, tx global/ops/taxonomy, OD-008 | PASS (Proposed) | Consistent. |
| Event deduplication semantics | `event_receipt` model/§9.3, ERD 1/3, tx op 10/taxonomy, OD-013 | PASS WITH LIMITATIONS | Connector-specific fallback details open. |
| Lifecycle and lineage semantics | Asset lifecycle/merge/split/tombstone/typed lineage in model/ERD 2/tx ops 6–8 | PASS (Proposed) | Consistent. |
| Open Decision IDs and statuses | OD-001–OD-013 in open decisions doc, references in model/ERD/tx/changelog | PASS | All 13 present; statuses proposed/open/partial as documented; no invented approvals. |
| Proposed versus approved design statements | Principal docs and changelog consistently label recommendations as Proposed/not approved where applicable | PASS | ADR 0006 remains Proposed. |
| ERD entity coverage vs logical entity catalogue | Mermaid entity extraction vs catalogue and omission notes | PASS WITH LIMITATIONS | 40 unique ERD entities found in 4 diagrams (see Mermaid validation). ERD and model explicitly document intentionally omitted/simplified catalogue entities; named omitted entities align with 10 core items commonly cited (`AI_INTERACTION_AUDIT`, `PROCESSING_WORK_ITEM`, `AI_PROVIDER_POLICY_CONSENT_REFERENCE`, `AI_PROVIDER_SECRET_REFERENCE`, `AI_USAGE_BUDGET_ACCOUNTING`, `DETECTION_RULE`, `DETECTION_RULE_VERSION`, `INTEGRATION_CONFIGURATION`, `THREAT_INTELLIGENCE_REFERENCE`, `ASSET_INVENTORY_OBSERVATION`) plus noted simplifications (e.g. reservation/evidence/support detail multiplicities) — coverage claim is reasonable but should be read against the explicit omission lists. |
| Obsolete terminology or superseded design references | Searched for `from_asset_or_op_ref` and polymorphic lineage usage | PASS | No current obsolete attribute/relationship definition found in principal model/ERD/tx; references are corrective/historical explanations. |

## Mermaid validation results

| Check | Method | Result | Evidence/notes |
|---|---|---|---|
| Mermaid `erDiagram` block count | Static parse of `docs/POSTGRESQL_LOGICAL_ERD.md` fenced ` ```mermaid ` blocks | **PASS** | 4 Mermaid blocks found. |
| Mermaid diagram declarations | Static search for `erDiagram` | **PASS** | `erDiagram` declarations present in Mermaid blocks (5 token occurrences observed including diagram content context). |
| Unique ERD entities defined in Mermaid blocks | Regex extraction of entity definitions (`ENTITY {`) across blocks | **PASS** | 40 unique entities: `ALERT`, `ASSET`, `ASSET_DATA_SOURCE`, `ASSET_IDENTITY_CLAIM`, `ASSET_LICENSE_EVENT`, `ASSET_LICENSE_RESERVATION`, `ASSET_LIFECYCLE_EVENT`, `ASSET_LINEAGE_LINK`, `ASSET_MERGE_OPERATION`, `ASSET_SPLIT_OPERATION`, `ASSET_TOMBSTONE`, `AUDIT_EVENT`, `DATA_SOURCE`, `EVENT_RECEIPT`, `EVENT_SCHEMA_REFERENCE`, `EVIDENCE_CUSTODY_EVENT`, `EVIDENCE_OBJECT_VERSION`, `EVIDENCE_TRANSITION_AUTHORIZATION`, `EXTERNAL_IDENTITY_SUBJECT`, `FORENSIC_EVIDENCE_RECORD`, `IDENTITY_OPERATION_IDEMPOTENCY_LEDGER`, `IDENTITY_RESOLUTION_CASE`, `INCIDENT_CASE`, `MEMBERSHIP_ROLE_ASSIGNMENT`, `OUTBOX_ATTEMPT`, `OUTBOX_MESSAGE`, `ROLE`, `ROLE_PERMISSION`, `SECURITY_EVENT`, `SOURCE_DEVICE_FINGERPRINT_ALIAS`, `SOURCE_DEVICE_KEY`, `SUBSCRIPTION_ENTITLEMENT`, `SUPPORT_ACCESS_APPROVAL`, `SUPPORT_ACCESS_GRANT`, `TENANT`, `TENANT_AI_PROVIDER_CONFIGURATION`, `TENANT_CONFIGURATION`, `TENANT_LICENSE_USAGE_STATE`, `TENANT_MEMBERSHIP`, `VULNERABILITY_FINDING`. |
| ERD entities represented in logical catalogue | Name-normalized comparison against model catalogue headings/rows | **PASS WITH LIMITATIONS** | All 40 ERD entities map to catalogue concepts/entries; prior catalogue duplication reduced clarity (corrected). |
| Intentionally omitted/simplified catalogue entities documented | `docs/POSTGRESQL_LOGICAL_ERD.md` “Intentionally omitted or simplified…” and `docs/POSTGRESQL_LOGICAL_DATA_MODEL.md` §9.6 | **PASS WITH LIMITATIONS** | Explicitly documented; includes 10 named entities and additional simplified detail categories. |
| Mermaid syntax parser/renderer validation | Environment check for `mmdc`, `npx`, Mermaid libraries | **NOT VERIFIED (visual/parsing tool unavailable)** | No Mermaid renderer/parser CLI available in this environment. **Structural validation was performed; visual rendering was not performed.** Structural validation is **not** reported as visual validation. |

## Open Decision reassessment (OD-001–OD-013)

| OD | Current documented status | Internal consistency | Blocks Round 2 design? | Blocks only specific physical design details? | Can be explicitly bounded without unsupported assumption? |
|---|---|---|---|---|---|
| OD-001 | Open/Proposed (ADR 0006 Proposed; schema-level interpretations unresolved) | Consistent across OD register/model/tx/changelog | **Partial** (core accepted licensing/identity schema finalization) | Yes, especially physical constraints/invariants tied to accepted ADR semantics | Yes, by treating ADR 0006 semantics as Proposed and excluding unapproved enforcement/constraint decisions |
| OD-002 | Open/Proposed (Alternative A recommended, not approved) | Consistent | **Yes (targeted blocker)** for physical identity binding tables/PK-FK/uniqueness/update authority | Yes | Yes, by documenting recommended model but deferring final physical binding schema until approval |
| OD-003 | Open/Proposed (pending reservation/capacity accounting unresolved) | Consistent | **Partial** | Yes (reservation/counter schema and quota effects) | Yes, by modeling reservation as optional/proposed and excluding final accounting implementation |
| OD-004 | Open/Proposed (counter semantics unresolved) | Consistent | **Yes for licensing accounting implementation** (not all structural tables) | Yes | Yes, by excluding finalized quota enforcement/counter equations from physical design commitments |
| OD-005 | Open/Proposed (merge/split approval authority/evidence unresolved) | Consistent | **Partial** | Yes (workflow/authorization enforcement details) | Yes, by preserving auditable operation records and bounding approval workflow design |
| OD-006 | Open/Proposed (fingerprint protection/key custody/rotation unresolved) | Consistent | **Partial** | Yes (sensitive-data handling, key refs, migration procedures) | Yes, by keeping alias/version metadata logical and deferring custody/crypto operational design |
| OD-007 | Open/Proposed (reinstall/re-enrollment behavior unresolved) | Consistent | **Partial** | Yes (enrollment/binding lifecycle constraints) | Yes, by maintaining identity distinctions and bounding lifecycle mappings |
| OD-008 | Open/Proposed (idempotency contract details/approval unresolved; A recommended default) | Consistent | **Yes (targeted blocker)** for physical idempotency constraints and transaction templates | Yes | Yes, by adopting proposed contract as design baseline while excluding unapproved staged exceptions/final templates |
| OD-009 | Open/Proposed (outbox lease/fencing/replay/unknown-delivery behavior unresolved) | Consistent | **Partial** | Yes (worker-processing physical schema/runtime behavior) | Yes, by modeling states/metadata logically and excluding finalized runtime parameters |
| OD-010 | Open/Proposed (evidence retention/legal hold/deletion unresolved) | Consistent | **Partial (major for compliant evidence lifecycle)** | Yes | Yes, by separating metadata/custody/transition concepts and deferring policy-driven lifecycle enforcement |
| OD-011 | Open/Proposed (AI consent/classification/budget/policy unresolved) | Consistent | **Partial** | Yes (enforceable AI-governance schema/policy details) | Yes, by enforcing documented external-SaaS boundaries and deferring consent/budget policy specifics |
| OD-012 | Open/Proposed (retention/workload/partitioning assumptions unresolved) | Consistent | **Partial** | Yes (physical partition/retention/storage design) | Yes, by treating capacity/retention as assumptions and excluding finalized partitioning commitments |
| OD-013 | Open/Partial/Proposed (connector-specific namespace/fallback behavior unresolved) | Consistent | **Partial** (connector-dependent) | Yes (supported-connector uniqueness constraints and ingestion acceptance rules) | Yes, by bounding to explicitly documented namespace model and excluding unapproved connector fallback behavior |

**Reassessment notes:** No decision status was changed. OD-002 and OD-008 remain the primary targeted technical blockers for physical identity/licensing/idempotency design finalization; OD-001/003/004 constrain accounting/accepted-schema semantics; OD-013 must be approved or explicitly bounded per supported connector. All other ODs can be explicitly bounded for a limited Round 2 design scope without unsupported assumptions.

## README correction details

**File corrected:** `dist/cares-external-audit/README.md` (local audit package README used for publication)

**Issues found (stale/inaccurate content):**
- Stated “Remote GitHub publication could not be completed…” and implied current publication unavailable due to missing Git repository/remote configuration.
- Did not identify repository, publication branch, commit, or direct file URLs for the actual published branch.

**Corrections applied:**
- Added accurate publication destination: repository `https://github.com/clarusinnovaceteknologi/cares`, branch `audit/postgresql-round1-1-publication`, branch URL, and initial publication commit `888905d8aef8bf6eb2e874cf9804a239f0f6f51a`.
- Added direct blob URLs for the three published package files on the publication branch.
- Distinguished historical packaging-time situation (workspace did not expose Git repository/source commit SHA at original package creation) from subsequent successful GitHub publication; preserved historical packaging date and “Source Git commit SHA: Not available at packaging time” fact.
- Removed/corrected statements implying current publication failure; stated README correction is made via later commit preserving history (no rewrite).
- Added explicit external accessibility statement: verified in-environment via GitHub repository tools; unauthenticated external accessibility not independently verified; if private, authorized GitHub access required; no visibility change made.
- Did **not** claim original ZIP was built from a known Git commit and did **not** claim independent verification beyond checks actually performed.

**Technical design documents:** not modified for README consistency. **Historical artifacts/history:** preserved (correction intended as new commit).

## Narrowly scoped essential documentation correction (non-README)

| File | Issue | Correction | Rationale | Scope/limits |
|---|---|---|---|---|
| `docs/POSTGRESQL_LOGICAL_DATA_MODEL.md` | Duplicate/misplaced catalogue entity rows remained in domain sections and additional SOC entities section (including duplicate `role_permission`, `outbox_attempt`, `tenant_configuration`, repeated identity/lineage rows and misplaced `data_source` entry), creating internal catalogue inconsistency and reducing authoritative clarity | Removed 9 duplicate/misplaced catalogue rows while preserving canonical Round 1.1 definitions (kept normalized `role_permission`/`membership_role_assignment` distinction, canonical `tenant_configuration`, primary `outbox_message`/`outbox_attempt` definitions, and authoritative identity/lineage entities in appropriate sections). Remaining backticked-name repetitions are section 9.5 normalization comparison rows (different purpose), not duplicate catalogue definitions. | Essential to eliminate clear documentation inconsistency in the authoritative logical catalogue and support cross-document/ERD consistency review; no change to intended Round 1.1 technical semantics | Narrowly scoped edit; no DDL/migration/app code; no ADR/status/approval/roadmap changes; no broad architectural redesign |

## Remaining issues and limitations

- **OD approvals unresolved:** OD-001–OD-013 remain open/proposed/partial as applicable; no formal approvals obtained or invented.
- **ADR 0006 Proposed:** schema-level licensing semantics not accepted as approved physical-design authority.
- **Mermaid visual rendering not performed:** renderer/parser CLI unavailable; structural validation only.
- **Remote ZIP parity not byte-verified:** published branch file presence verified via GitHub tools, but remote `CARES_DOCUMENTATION_HTML.zip` binary contents/SHA-256 were not independently downloaded/compared in this environment.
- **Repository visibility/external unauthenticated access not independently verified:** may require authorized GitHub access if private.
- **Export manifest/reporting details:** prior manifest used different key names than some earlier summaries; regenerated export/manifest must be treated as authoritative after this correction run.
- **Physical design details deferred:** no indexes, partitioning, RLS policies, constraints syntax, role grants, functions/triggers/procedures, or migration sequencing designed/implemented.

## Evidence supporting major findings

- **Binding (A):** `docs/POSTGRESQL_LOGICAL_DATA_MODEL.md` (`asset_data_source`, `source_device_key`, `source_device_fingerprint_alias`, §9.1), `docs/POSTGRESQL_LOGICAL_ERD.md` (conventions, ERD 1/2, explanation), `docs/POSTGRESQL_TRANSACTION_BOUNDARIES.md` (global constraints, ops 1–4,6–7, Round 1.1 notes), `docs/POSTGRESQL_SCHEMA_OPEN_DECISIONS.md` (OD-002), `docs/POSTGRESQL_LOGICAL_MODEL_ROUND1_1_CHANGELOG.md` (finding 1).
- **Idempotency (B):** model `identity_operation_idempotency_ledger` and §9.2, ERD 2 ledger fields, tx global constraints/ops/taxonomy and Round 1.1 notes, OD-008, changelog finding 2.
- **Event dedup (C):** model `event_receipt` and §9.3, ERD 1/3 receipt namespace fields, tx op 10 and taxonomy, OD-013, changelog finding 3.
- **Lineage (D):** model `asset_lineage_link`/`asset_merge_operation`/`asset_split_operation` and §9.4, ERD 2 typed lineage relationships/attributes, tx ops 6–7 and notes, OD register lineage correction note, changelog finding 4; search confirmed no `from_asset_or_op_ref` attribute in ERD.
- **Naming/responsibilities (E):** model 3.1/3.4/3.5/3.6/§9.5, ERD 1/3/4 and omission notes, changelog finding 5; duplicate-catalogue issue identified by entity-row scan and corrected.
- **Cross-doc/ERD coverage:** 4 Mermaid blocks / 40 unique ERD entities extracted; ERD/model omission sections; tx operation count (13) verified by headings; OD-001–OD-013 present.
- **Publication correction:** local and remote README text compared (stale publication-failure statement present in commit `888905d...`), git branch/commit state verified (`audit/postgresql-round1-1-publication` tracking origin at `888905d...`), ZIP integrity/hash presence verified locally.

## Final recommendation for Round 2 readiness

**Recommendation:** **READY FOR ROUND 2 WITH EXPLICITLY BOUNDED EXCLUSIONS**

**Basis (inspected artifacts):** principal Round 1.1 Markdown sources, ERD/transactions/open decisions/changelog, supporting architecture/ADR references, export index/manifest and ZIP integrity/presence checks, and publication package state.

**Issues that block the entire Round 2 design:** **None identified** for proceeding with *bounded* Round 2 logical-to-physical design work as a design exercise, provided exclusions are respected.

**Issues that block only specific physical design decisions (explicit exclusions):**
- **OD-002 (targeted blocker):** final physical identity binding table design (authoritative ownership, PK/FK/uniqueness, update authority, dependent projection materialization) pending formal technical approval.
- **OD-008 (targeted blocker):** final physical idempotency ledger constraints/state representation and transaction templates pending formal approval of scope, canonicalization/hash, state machine/terminal rules, retention/reconciliation, and any staged exceptions.
- **OD-001, OD-003, OD-004:** finalized licensing/quota accounting enforcement semantics, reservation/counter physical representation, and accepted ADR 0006 schema interpretations pending ADR/owner/commercial approvals.
- **OD-013 (connector-dependent partial blocker):** physical dedup uniqueness constraints and ingestion acceptance/fallback rules for supported connectors pending approved namespace/fallback behavior.
- **OD-005, OD-006, OD-007, OD-009, OD-010, OD-011, OD-012:** block only specific workflow/authorization, sensitive-data/key-custody/migration, enrollment lifecycle, outbox runtime/reconciliation, evidence lifecycle, AI governance enforcement, and partition/retention/storage physical design details as applicable.

**Issues that can be deferred safely (with bounds):** optional dependent `source_device_key` projection materialization choice (if kept consistent with authoritative binding model), `processing_work_item` modeling, fine-grained RBAC/catalog expansions, physical optimization/partitioning specifics, and detailed connector fallback implementations until connector onboarding decisions are made — provided they do not violate documented invariants.

**Decisions requiring formal project-owner (and/or technical/security/privacy/legal/commercial) approval:** OD-001–OD-013 as categorized in the open decisions register (especially OD-001/002/003/004/005/006/008/010/011 and connector approvals affecting OD-013); **ADR 0006 acceptance** remains a governance/owner decision.

**Explicit exclusions for Round 2 authorization context:** no DDL/migrations/database objects/RLS policies/roles/grants created; no unapproved licensing/accounting semantics implemented; no unapproved idempotency/connector-fallback behavior finalized as accepted; no ADR status changes; no invented approvals.

*End of report. Stop after audit and publication correction; do not start Round 2 without explicit project-owner authorization.*
