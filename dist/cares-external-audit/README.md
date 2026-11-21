# CARES PostgreSQL Logical Model Round 1.1 — Temporary External Audit Publication

- **Purpose:** Temporary, read-only publication for external technical review.
- **Contents:** Latest available CARES PostgreSQL Logical Model Round 1.1 outputs in this workspace at the time of packaging.
  - `copilot.txt` — actual Round 1.1 execution report.
  - `CARES_DOCUMENTATION_HTML.zip` — complete HTML documentation export (including documentation index and manifest).
- **Scope/limitations:** No implementation approval or ADR status change is implied by publication. Artifacts are documentation/design outputs only (not DDL, migrations, database implementation, application code, tests, or security/production validation evidence).
- **Publication date:** 2026-11-21T15:33:19Z
- **Source Git commit SHA:** Not available (workspace `/home/ubuntu/cares` is not a Git repository; no commit provenance).

## Verification summary (local packaging)
- Published files verified non-empty.
- ZIP integrity tested (`zipfile.testzip()` returned no bad member).
- ZIP confirmed to include documentation index/manifest and all five required Round 1.1 target HTML documents:
  - `POSTGRESQL_LOGICAL_DATA_MODEL.md.html`
  - `POSTGRESQL_LOGICAL_ERD.md.html`
  - `POSTGRESQL_TRANSACTION_BOUNDARIES.md.html`
  - `POSTGRESQL_SCHEMA_OPEN_DECISIONS.md.html`
  - `POSTGRESQL_LOGICAL_MODEL_ROUND1_1_CHANGELOG.md.html`

## Access note
Remote GitHub publication could not be completed from this workspace because no Git repository or GitHub remote is configured. External reviewers will require access only if/when the package is published to an authorized GitHub location; this local package must not be exposed through an unauthorized public mirror.
