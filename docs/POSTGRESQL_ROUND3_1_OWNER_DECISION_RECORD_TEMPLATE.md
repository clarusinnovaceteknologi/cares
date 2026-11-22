# CARES PostgreSQL Round 3.1 — Owner Decision Record Template

**Status:** Template only; **NOT A DECISION, NOT AN APPROVAL, NOT AN AUTHORIZATION**. This template is provided for the project owner to record an explicit decision. **Do not pre-fill owner selections.** No field below constitutes a decision until completed, dated, and confirmed by the authorized owner (and any required co-approvers) in a recorded repository artifact.

**Usage rules (preserved):**
- Recording a decision does **not** authorize implementation unless a separate explicit implementation authorization record is completed for a narrowly defined increment.
- A Copilot recommendation is **not** an owner decision. Silence or publication of governance documents is **not** approval.
- OD/PD identifiers and source statuses must remain traceable; do not close an item without explicit recorded owner action and required evidence.

---

## Owner Decision Record

| Field | Owner input (leave blank until decided) |
|---|---|
| **Decision ID** |  |
| **Related increment(s) / scope affected (if any)** |  |
| **Source document(s) / baseline reference** |  |
| **Decision question** |  |
| **Decision status** | `Decided` / `Deferred` / `Rejected (current option)` / `Further analysis required` (select one when recorded) |
| **Selected option** |  |
| **Rationale** |  |
| **Accepted risks and constraints** |  |
| **Rejected alternatives (and reasons)** |  |
| **Conditions / prerequisites for effect** |  |
| **Dependencies (OD/PD/ADR/approvals/validations)** |  |
| **Required follow-up actions and owners** |  |
| **Effective date** |  |
| **Owner name / role** |  |
| **Owner confirmation (explicit statement/signature reference)** |  |
| **Additional approvers required (security/legal/commercial/DBA/architecture, if applicable)** |  |
| **Evidence / links to supporting records** |  |

## Deferral or further-analysis record (use if not decided)

| Field | Owner input (leave blank until recorded) |
|---|---|
| **Reason for deferral / analysis request** |  |
| **Information or validation needed** |  |
| **Responsible party** |  |
| **Target review date or trigger** |  |
| **Interim restrictions** |  |

## Traceability and non-authorization note

- This record documents an owner decision status only for the identified item. It must not be interpreted as authorization for I-00–I-14 or any implementation work unless a separate [POSTGRESQL_ROUND3_1_IMPLEMENTATION_AUTHORIZATION_TEMPLATE.md](./POSTGRESQL_ROUND3_1_IMPLEMENTATION_AUTHORIZATION_TEMPLATE.md) record explicitly authorizes a defined increment.
- Preserve existing architectural/security invariants and unresolved decision boundaries as stated in [POSTGRESQL_ROUND3_1_OWNER_DECISION_GATE.md](./POSTGRESQL_ROUND3_1_OWNER_DECISION_GATE.md).
