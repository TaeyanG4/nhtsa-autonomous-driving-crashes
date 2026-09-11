# Autonomous Driving Crash Reports — NHTSA

[English](README.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | [简体中文](README.zh-CN.md)

Reproducible Kaggle release of the **current third-amended NHTSA Standing General Order (SGO) crash-reporting regime** for ADS, Level 2 ADAS, and Other/Unknown reports.

## Live release

- Kaggle dataset: https://www.kaggle.com/datasets/taeyangg4/nhtsa-autonomous-driving-crashes
- Showcase notebook: https://www.kaggle.com/code/taeyangg4/what-do-reported-self-driving-crashes-look-like
- Kaggle version / status: `1 / Ready`
- Kaggle Usability: `10.0 / 10`
- Data Explorer metadata: `data.csv` description `1/1` exact; column descriptions `123/123` exact

The Kaggle notebook card uses the shorter title **“What Do Reported Self-Driving Crashes Look Like?”** to satisfy Kaggle's title-length constraint. The notebook's H1 preserves the intended long-form title **“What Do Reported Autonomous-Driving Crashes Look Like?”**.

## Release design

The public Kaggle product is intentionally simple: one `data.csv`. Each row is one NHTSA `Report ID`, using the highest numeric `Report Version` available in the current NHTSA source files. All 116 current source fields are preserved in snake_case and seven transparent provenance/convenience columns are added.

V1 does **not** force the 2021–June 2025 archive into the current schema. The pilot found 116 current columns versus 137 archive columns, with only 89 names in common and multiple material concept/grain changes. Historical harmonization is deferred until it has a clear user benefit and defensible mappings.

## Current measured release

- Source snapshot ID: `20260827`
- Current source version rows: 3,413
- Canonical latest Report IDs: 3,263
- Columns: 123
- Incident month coverage in selected rows: 2023-01 through 2026-07
- Current-regime report submission coverage: 2025-06 through 2026-07
- Duplicate `(Report ID, Report Version)` source pairs: 0
- Latest-version selection mismatches: 0
- Public narratives present: 3,262 / 3,263 rows

Incident dates can predate June 16, 2025 because later/current-regime report versions can describe older incidents. `source_regime`, not incident date, identifies the schema/reporting regime.

## Critical interpretation limits

Raw reporting-entity or vehicle-make counts are **not crash rates and are not safety rankings**. Reporting entities differ in telemetry, crash awareness, fleet size, mileage/exposure, operating domain, and reporting obligations. ADS and Level 2 ADAS also have different reportability criteria. A real-world crash can have multiple reports; this project preserves NHTSA's `Same Incident ID` but never silently merges reports on that field.

## Source and rights

Source of truth: NHTSA Standing General Order on Crash Reporting. The pipeline only ingests NHTSA's official public CSV releases and preserves the agency's PII/CBI redactions. Kaggle is conservatively marked `Other` license because some submitted narrative/content originates with reporting entities, so the project does not make a blanket public-domain claim over every field.

See `research/source_rights.md` for the full rights/provenance gate and `research/pilot_decision.md` for the regime decision.

## Rebuild

Use Python 3.12+ on Windows with UTF-8 I/O:

```powershell
$env:PYTHONUTF8='1'
$env:PYTHONIOENCODING='utf-8'
python -m pip install -r requirements.txt
python src\pipeline.py all
python src\build_product.py
python -m pytest -q
python -m ruff check .
```

Stages are restartable and persisted separately:

```text
discover -> snapshot -> parse -> rights gate -> normalize -> QA -> manifest
```

Raw source snapshots are under `data/raw/`, normalized intermediates under `data/derived/`, the one public data artifact under `release/data.csv`, and detailed research/QA/provenance under `research/`, `qa/`, and `state/`.

## Research and QA

- `research/market_validation.md` — analog datasets, adoption evidence, pre-pilot scorecard
- `research/source_rights.md` — official-source discovery, regime semantics, redistribution basis
- `research/pilot_decision.md` — measured pilot, schema differences, re-score, V1 scope decision
- `qa/qa_report.json` — source-to-output reconciliation, versions, IDs, dates, missingness, narratives, anomalies
- `qa/column_mapping.json` — exact source-to-release column mapping and descriptions
- `qa/release_manifest.json` — generated release/source checksums and Git SHA (not committed; regenerated for each release)

## Showcase notebook

`notebooks/what-do-reported-autonomous-driving-crashes-look-like.ipynb` is the public Kaggle notebook. It demonstrates time trends, ADS/Level 2 categories, report/vehicle distributions, road/weather/crash characteristics, severity, and narrative-text exploration while repeatedly distinguishing report counts from safety rates.
