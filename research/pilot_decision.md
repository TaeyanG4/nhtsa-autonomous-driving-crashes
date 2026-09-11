# Phases 3-5 - Pilot, canonical design, and re-score

The machine-readable pilot is `qa/pilot_report.json`.

## Measured pilot

- 8 official pilot files (6 CSVs + 2 data dictionaries), **14,476,312 bytes** total.
- CSV payload: **13,529,114 bytes**, **13,333 rows**.
- Third-amended/current: **3,413 report-version rows**, **3,263 Report IDs**, 116 columns.
- Pre-third-amendment archive: **9,920 report-version rows**, **8,160 Report IDs**, 137 columns.
- No duplicate `(Report ID, Report Version)` pairs in either regime.
- Current regime: 128 Report IDs have multiple observed versions; maximum Report Version is 5.
- Archive: 1,549 Report IDs have multiple versions; maximum Report Version is 9.
- **38 Report IDs occur in both archive and current files.** In these cases the current files contain later versions (for example archive v1 -> current v2). This explains why a current-only file can legitimately contain Report Version > 1 without carrying every earlier version.
- Current source rows span incident months **2023-01 through 2026-07**, because post-amendment updates can describe older incidents; current report submissions span **2025-06 through 2026-07**. Reporting regime must therefore be derived from source publication/schema, not from incident date.
- Archive incident dates include a 1900-01 anomaly and 3,562 blank/unparseable values; this is preserved as a QA anomaly rather than silently removed.
- Current latest-report records have 5 Same Incident IDs that link multiple distinct Report IDs (11 latest rows). Those reports are not collapsed.
- Same Incident ID changes across versions for 7 current Report IDs and 30 archive Report IDs, reinforcing the need to retain the latest source value rather than assuming the linkage key is immutable.
- Narrative availability is essentially complete in current ADS/ADAS/Other files (ADS 100%; Level 2 ADAS 99.95%; Other 100%). Archive Other is only 2.22% nonblank.
- Estimated user-facing CSV size is roughly **4.3-7.4 MB** for current-regime source rows and **13.5-23.0 MB** if all regimes were naively combined.

## Schema / semantic finding

The current schema has 27 fields not in the archive; the archive has 48 fields not in the current schema, with only 89 names in common. More importantly, several concepts changed rather than merely being renamed: the prior `ADS Equipped?` framing is not the current category basis; `Engagement Status` appears in the new form; roadway/weather fields were restructured; air-bag/tow/belt fields changed grain; old mileage, notice-date, lighting, posted-speed, permitting, and investigating-officer details disappeared.

Forcing 2021-2026 into one deceptively uniform schema would either create many regime-specific nulls or silently equate fields whose meaning changed. That is unnecessary for the smallest high-adoption V1.

## Canonical V1 design

**V1 is narrowed to the clean third-amended reporting regime.** It uses all three current NHTSA buckets (ADS, Level 2 ADAS, and Other/Unknown) so source coverage is complete, but every row carries the source bucket and `automation_system_engaged` field.

One row in `data.csv` represents the **latest available version of one NHTSA Report ID** in the current third-amended files:

1. Union the three current CSVs without semantic remapping between buckets (same 116-column schema).
2. Parse `Report Version` numerically.
3. For each `Report ID`, select the row with the highest `Report Version`.
4. Preserve `Report ID`, selected `Report Version`, `Same Incident ID`, `Same Vehicle ID`, original source values, source bucket, source file, source URL, and reporting-regime provenance.
5. Do not use `Report Submission Date` to choose a version; NHTSA defines it as the first submission month/year.
6. Do not collapse rows by `Same Incident ID`; it remains a source-provided linkage field, not a fabricated crash-level primary key.
7. Add only transparent convenience fields such as normalized incident/report month values; never overwrite the source-form field.

## Re-score

| Dimension | Score / 5 | Weighted points | Measured basis |
|---|---:|---:|---|
| Proven demand | 4 | 12/15 | Broad crash niche strong; direct SGO early traction |
| Distinctiveness / moat | 3 | 9/15 | Same official source exists elsewhere, but V1 is materially simpler and regime-explicit |
| Clear task | 5 | 10/10 | One-row-per-latest-report EDA/text workflow |
| Broad audience | 4 | 8/10 | US data with global AV/safety interest |
| Time-to-first-insight | 5 | 10/10 | Single CSV, ~3.3k rows expected |
| Source authority + rights | 5 | 10/10 | Official current NHTSA public/redacted release; rights gate passed |
| Freshness | 5 | 5/5 | Monthly source cadence |
| Rebuild efficiency | 5 | 5/5 | Three small CSVs for production V1 |
| Download/runtime friction | 5 | 5/5 | Few MB, ordinary notebook hardware |
| Portfolio diversification | 4 | 4/5 | AV + public safety + narratives |
| Notebook/visual hook | 5 | 10/10 | Strong trend/category/condition/severity/text visuals |
| **Total** |  | **88/100** |  |

## Decision

**GO — build and publish V1 using the third-amended SGO regime only.** Historical harmonization is explicitly deferred. A future historical V2 should be a separate, justified semantic-mapping project, not an automatic extension of this release.
