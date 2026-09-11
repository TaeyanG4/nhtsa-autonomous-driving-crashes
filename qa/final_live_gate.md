# Final live gate — 2026-09-11

## Live Kaggle dataset

- Dataset: `taeyangg4/nhtsa-autonomous-driving-crashes`
- Intended/current version: `1`
- Status: `Ready`
- Public root file: `data.csv` only
- Live bytes: `4,734,159`
- Local/live SHA-256: `9effcecb70f1e9922e26d83f7749fd984af87dee01479df54a283dc85867b66e` (exact match)
- Rows / columns: `3,263 / 123`
- License: `other`
- Expected update frequency: `monthly`
- Source URL metadata: NHTSA Standing General Order on Crash Reporting

## Showcase notebook

- Kaggle ref: `taeyangg4/what-do-reported-self-driving-crashes-look-like`
- Live status: `COMPLETE`
- Kaggle card title: `What Do Reported Self-Driving Crashes Look Like?`
- Notebook H1: `What Do Reported Autonomous-Driving Crashes Look Like?`
- The shorter card title is used because the requested long-form title exceeds Kaggle's kernel title-length constraint.

## Cover

Live 2:1 cover and live 1:1 card crop were downloaded from Kaggle and visually checked. The NHTSA SGO / ADS + Level 2 ADAS / vehicle-and-sensor focal content remains legible and centered in both crops.

## Data Explorer metadata limitation

Repository target coverage is one file description and 123 column descriptions. Before writing, the public Data Explorer schema was read back and verified at 123 columns with exact order. Live base type / extended type / order were captured. An official Kaggle SDK metadata-only write sent `data.csv` with the exact live byte count and all 123 column names/descriptions while intentionally omitting column `type` so Kaggle's inferred types would not be overwritten.

Post-write public Data Explorer readback shows:

- present file descriptions: `0 / 1`
- exact file descriptions: `0 / 1`
- present column descriptions: `0 / 123`
- exact column descriptions: `0 / 123`
- schema/type/order preserved: `true`

Kaggle CLI 2.2.4 and the current SDK accept the structured metadata write, but the public Data Explorer read model does not persist/expose the descriptions. Do not repeat identical CLI/SDK metadata writes merely to force Usability. The next supported escalation is an authenticated official Kaggle MCP client/token path; do not copy CLI bearer tokens, browser cookies, or credentials between clients.

## Current platform quality metric

Latest official CLI metadata readback during this gate reported `usabilityRating = 0.7058823529411765`. This is below the desired 10/10 baseline and is attributable to the unresolved Data Explorer description persistence gate. All content, file, notebook, cover, source, and repository gates can be completed independently without creating a new dataset version.

## End-of-session handoff

### Repository

- Public repository: `https://github.com/TaeyanG4/nhtsa-autonomous-driving-crashes`
- Branch: `main`
- Release-finalization commit before this handoff update: `0db9c36b55f62a74c7ef86019bf9778aa39a30e8`
- Tests: `pytest` 3/3 passed; Ruff passed; `git diff --check` passed; local notebook execution passed.
- Public documentation: `README.md`, `README.ko.md`, `README.ja.md`, and `README.zh-CN.md` are synchronized.

### Kaggle

- Owner/dataset: `taeyangg4/nhtsa-autonomous-driving-crashes`
- Version/status: `1 / ready`
- Live file: `data.csv` only, `4,734,159` bytes.
- Live/local SHA-256: exact match.
- Showcase notebook: `taeyangg4/what-do-reported-self-driving-crashes-look-like`, status `COMPLETE`.
- Launch baseline observed on 2026-09-11: `5` views, `3` downloads, `1` notebook; vote count was not returned by the current readback and is intentionally not guessed.
- Usability: `0.7058823529411765` (`7.06 / 10`).
- Data Explorer description coverage: file `0/1`, columns `0/123` present/exact after the supported CLI/SDK attempts.

### Release invariants

- Canonical public artifact: one `data.csv`.
- Grain: one row per NHTSA `Report ID`, selecting the highest numeric `Report Version` available in the current third-amended source snapshot.
- Release size: `3,263` rows × `123` columns.
- Source snapshot: `20260827`; current third-amended SGO regime effective 2025-06-16.
- Rights: use only official public NHTSA files, preserve PII/CBI redactions, Kaggle license `other`.
- `same_incident_id` is preserved as source linkage evidence but is not used to silently merge reports.
- Raw manufacturer/reporting-entity counts are not exposure-normalized crash rates or safety rankings.
- UTF-8/no-BOM is required for Kaggle metadata and public repository text.

### What worked

- Official Kaggle CLI for dataset create/status/files/metadata/download and notebook push/status/pull.
- Official Kaggle SDK for a controlled metadata-only write while preserving live file bytes and inferred schema.
- Public Kaggle Data Explorer readback for verifying 123-column order and inferred type/extended-type preservation.
- Live artifact download verified exact content hash equality.

### What failed / do not repeat unchanged

- Repeating CLI/SDK Data Explorer description writes does not make file/column descriptions appear in the current live read model; post-write coverage remained `0/1` and `0/123`.
- Generic `mcp-remote` OAuth on this Windows host generated a callback URI with an IP/port that Kaggle rejected against its strict redirect allowlist. Do not retry that unchanged.
- Do not create a new dataset content version merely to force metadata/Usability refresh.

### Authentication constraints

- Keep using official Kaggle CLI credential storage for CLI/SDK operations.
- For a future MCP escalation, use a current Kaggle-supported authenticated MCP client or Kaggle-generated MCP token through user-managed secret injection.
- Never copy CLI bearer tokens, browser cookies, OAuth access/refresh tokens, or authorization headers between clients.

### Portfolio sync

- Public portfolio: `https://github.com/TaeyanG4/kaggle-dataset-portfolio`
- Synced commit: `75ea6b580d40a99b1d4bf01efd082e11903aa3e1`
- Portfolio records the live launch baseline, Usability 7.06, showcase notebook, unresolved Data Explorer blocker, and the ~1-week adoption checkpoint as the next action.

### Next action

At the ~1-week checkpoint, refresh views/downloads/votes and external/notebook reuse before changing positioning or publishing another content version. Escalate the Data Explorer description blocker only through a current officially supported authenticated Kaggle MCP path.
