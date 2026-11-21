# CARES PostgreSQL Logical Model Round 1.1 — External Audit Publication

## Purpose
Temporary, read-only publication of the CARES PostgreSQL Formal Schema Design — Round 1.1 audit package for external technical review.

## Contents
- `README.md` — this publication README.
- `copilot.txt` — Round 1.1 execution report artifact as packaged (updated in subsequent correction commits when applicable).
- `CARES_DOCUMENTATION_HTML.zip` — complete HTML documentation export package (including documentation index and manifest).

## Scope and limitations
- **Documentation/design only.** No implementation approval or ADR status change is implied.
- Not DDL, migrations, database implementation, application code, tests, or security/production validation evidence.
- Proposed design elements and recommendations remain subject to required technical/product/owner/security/privacy/legal/commercial approvals as documented.

## Publication and provenance
- **Repository:** https://github.com/clarusinnovaceteknologi/cares
- **Publication branch:** `audit/postgresql-round1-1-publication`
- **Branch URL:** https://github.com/clarusinnovaceteknologi/cares/tree/audit/postgresql-round1-1-publication
- **Initial publication commit (three-file audit package):** `888905d8aef8bf6eb2e874cf9804a239f0f6f51a`
- **Original package creation date (local packaging):** 2026-11-21T15:33:19Z
- **Source Git commit SHA for original package contents:** Not available at packaging time. The original local package was prepared in a workspace that did not expose a Git repository or source commit SHA/provenance for the documentation state being packaged. This historical fact is preserved; it does **not** mean the package was never published to GitHub.

### Historical packaging note (preserved) and subsequent publication correction
- At original packaging time, the local workspace `/home/ubuntu/cares` did not expose a configured Git repository/remote, so remote publication could not be completed in that initial step. That historical packaging-time situation is preserved as provenance context.
- The audit package was subsequently published to the repository and branch listed above. This README has been corrected in a later commit to reflect actual publication state; publication history is preserved through new commits (no history rewrite).

## Local packaging verification (original package preparation)
- Published files were verified non-empty.
- ZIP integrity was tested (`zipfile.testzip()` returned no bad member).
- ZIP was confirmed to include documentation index/manifest and all five required Round 1.1 target HTML documents:
  - `POSTGRESQL_LOGICAL_DATA_MODEL.md.html`
  - `POSTGRESQL_LOGICAL_ERD.md.html`
  - `POSTGRESQL_TRANSACTION_BOUNDARIES.md.html`
  - `POSTGRESQL_SCHEMA_OPEN_DECISIONS.md.html`
  - `POSTGRESQL_LOGICAL_MODEL_ROUND1_1_CHANGELOG.md.html`
- Original package SHA-256 hashes recorded at packaging time:
  - `copilot.txt`: `1a06f38285fbabc7e1b77d2bce90c38b928bc95a02500112d3b4984d59c0c4e5`
  - `CARES_DOCUMENTATION_HTML.zip`: `b8ef7f11b1b7c6f9e8381896f121dc2d7200911c3fc9572f850a71f3c02049c6`

## Direct file locations (publication branch)
- `README.md`: https://github.com/clarusinnovaceteknologi/cares/blob/audit/postgresql-round1-1-publication/dist/cares-external-audit/README.md
- `copilot.txt`: https://github.com/clarusinnovaceteknologi/cares/blob/audit/postgresql-round1-1-publication/dist/cares-external-audit/copilot.txt
- `CARES_DOCUMENTATION_HTML.zip`: https://github.com/clarusinnovaceteknologi/cares/blob/audit/postgresql-round1-1-publication/dist/cares-external-audit/CARES_DOCUMENTATION_HTML.zip

## External accessibility
- Repository, branch, commit, and file presence were verified in this environment using GitHub repository inspection tools during publication/audit correction work.
- Unauthenticated external accessibility (e.g. reviewers without GitHub access) was **not independently verified** in this environment. If the repository is private, external reviewers require authorized GitHub access. No repository visibility change was made.
- Updated file hashes and any additional verification results from subsequent correction/export regeneration are recorded in `copilot.txt` and `docs/POSTGRESQL_LOGICAL_MODEL_ROUND1_1_FINAL_AUDIT.md` (when included in the export/package).
