# CARES PostgreSQL Round 3.1 — Implementation Authorization Template

**Status:** Template only; **NOT AN AUTHORIZATION, NOT AN APPROVAL, NOT A DECISION**. This is a separate explicit authorization instrument. **Leave all authorization fields unfilled** until and unless the authorized project owner completes and records them for a narrowly defined increment. No implementation is authorized by existence of this template or by any planning/governance document.

**Mandatory rules (preserved):**
- Authorization for one increment **does not** authorize subsequent increments.
- Authorization does not resolve OD/PD items, change ADR status, or waive prerequisites/exclusions.
- Any authorized work must preserve all non-negotiable invariants (trusted verified transaction-bound tenant context only; no client-supplied tenant IDs; no user-settable PostgreSQL GUC authorization; authoritative binding/immutable `source_device_key_id`; ledger/event-dedup separation; typed lineage; no exactly-once external delivery; MELIRA external SaaS constraints; one unique monitored device = one licensed asset per tenant).
- If required prerequisites are unmet, authorization must not be issued.

---

## Implementation Authorization Record

| Field | Owner input (must remain blank until explicitly authorized) |
|---|---|
| **Authorization ID / record reference** |  |
| **Exact increment(s) authorized (I-00–I-14 identifiers only as applicable)** |  |
| **Scope summary (precise, bounded)** |  |
| **Target branch** |  |
| **Baseline commit SHA (exact)** |  |
| **Allowed changes (explicit list)** |  |
| **Prohibited changes / exclusions (explicit list)** |  |
| **Required prerequisites satisfied (OD/PD/ADR/approvals/validations/evidence references)** |  |
| **Environment and controls (non-production/isolated/change control/backup-recovery as required)** |  |
| **Acceptance criteria and required verification evidence** |  |
| **Rollback/recovery conditions** |  |
| **Authorization date** |  |
| **Authorized by (owner name/role and explicit confirmation)** |  |
| **Additional required approvers and confirmations (security/DBA/legal/compliance as applicable)** |  |
| **Expiration / revocation conditions (if any)** |  |

## Explicit statements (must remain true when completed)

- [ ] This authorization applies **only** to the exact increment(s) and scope listed above.
- [ ] This authorization for one increment **does not authorize subsequent increments**.
- [ ] No unresolved blocking OD/PD/ADR prerequisite for the authorized scope remains unmet (attach evidence).
- [ ] No implementation outside allowed changes is permitted.
- [ ] Tenant-safe runtime behavior is not claimed unless separately validated and explicitly within authorized scope.

## Non-authorization notice

Until this record is fully completed and recorded by the authorized owner, **no implementation is authorized**.
