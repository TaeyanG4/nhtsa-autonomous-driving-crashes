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

## Data Explorer metadata completion

Repository target coverage is one file description and 123 column descriptions. Before writing, the public Data Explorer schema was read back and verified at 123 columns with exact order. Live base type / extended type / order were captured. CLI/SDK metadata writes did not persist this structured Data Explorer metadata, and the hosted MCP wrapper could not safely bind the nested metadata payload.

The final supported escalation used an explicitly authorized same-origin Kaggle browser action. The script used the Kaggle page's already-authenticated Data Explorer SDK client, performed a one-column `report_id` smoke write/readback first, and only then wrote the `data.csv` description plus all 123 column descriptions while preserving the live type and extended-type values. No browser cookies, OAuth tokens, authorization headers, or KGAT values were extracted or replayed.

Immediate same-origin Data Explorer readback after the batch shows:

- present file descriptions: `1 / 1`
- exact file descriptions: `1 / 1`
- present column descriptions: `123 / 123`
- exact column descriptions: `123 / 123`
- schema/type/order preserved: `true`

Kaggle CLI 2.2.4 and the current SDK accepted the structured metadata write but did not persist the Data Explorer descriptions in this release. Do not repeat those writes for this backend/client state. The successful path was the version-specific same-origin Data Explorer SDK update described above.

## Current platform quality metric

After the same-origin Data Explorer metadata update, Kaggle displayed **Usability 10 / 10**. The browser-side completion readback also returned the target file description and all 123 target column descriptions exactly. No new dataset content version was created.

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
- Usability: `10 / 10`.
- Data Explorer description coverage: file `1/1` present/exact, columns `123/123` present/exact.

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
- Authenticated same-origin Kaggle Data Explorer SDK update: one-column smoke write/readback, then one file description plus 123 exact column descriptions, with type/extended-type preserved.
- Live artifact download verified exact content hash equality.

### What failed / do not repeat unchanged

- Repeating CLI/SDK Data Explorer description writes did not make file/column descriptions appear in the live read model for this release; do not repeat that path unchanged.
- Hosted Kaggle MCP authentication succeeded, but the current `update_dataset_metadata` wrapper did not safely bind the required nested list payload for this task; do not retry the same wrapper payload unchanged.
- Generic `mcp-remote` OAuth on this Windows host generated a callback URI with an IP/port that Kaggle rejected against its strict redirect allowlist. Do not retry that unchanged.
- Do not create a new dataset content version merely to force metadata/Usability refresh.

### Authentication constraints

- Keep using official Kaggle CLI credential storage for CLI/SDK operations.
- The successful browser fallback relied only on the user's already-authenticated `kaggle.com` page and did not expose or transfer credentials.
- Never copy CLI bearer tokens, browser cookies, OAuth access/refresh tokens, KGAT values, or authorization headers between clients.

### Portfolio sync

- Public portfolio: `https://github.com/TaeyanG4/kaggle-dataset-portfolio`
- Synced commit: `827c06191ce9b6d5c364e30a81af73dabe2b9909`
- Portfolio records Usability 10.0, Data Explorer descriptions complete, the showcase notebook, and the ~1-week adoption checkpoint as the next action.

### Next action

At the ~1-week checkpoint, refresh views/downloads/votes and external/notebook reuse before changing positioning or publishing another content version. The Usability/Data Explorer quality gate is complete; do not spend additional release cycles on metadata unless a future Kaggle version or backend change regresses it.
