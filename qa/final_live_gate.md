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
