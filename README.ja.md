# Autonomous Driving Crash Reports — NHTSA

[English](README.md) | [한국어](README.ko.md) | **日本語** | [简体中文](README.zh-CN.md)

ADS、Level 2 ADAS、Other/Unknown report を対象とした **current third-amended NHTSA Standing General Order (SGO) crash-reporting regime** を、Kaggle 向けに再現可能な形で構築するプロジェクトです。

## Release 設計

公開 Kaggle product は意図的に単純化し、`data.csv` 1 ファイルのみを提供します。各行は 1 つの NHTSA `Report ID` で、current NHTSA source files に存在する最大の数値 `Report Version` を採用します。current source の 116 fields を snake_case のまま保持し、provenance / convenience 用の透明な 7 columns を追加します。

V1 は 2021年〜2025年6月 archive を current schema に無理に統合しません。Pilot では current 116 columns、archive 137 columns、共通名は 89 のみで、複数の重要な concept/grain 差も確認されました。Historical harmonization は、明確な user benefit と defensible mapping が得られるまで延期します。

## 現在の実測 Release

- Source snapshot ID: `20260827`
- Current source version rows: 3,413
- Canonical latest Report IDs: 3,263
- Columns: 123
- 選択行の incident month coverage: 2023-01 〜 2026-07
- current-regime report submission coverage: 2025-06 〜 2026-07
- Duplicate `(Report ID, Report Version)` source pairs: 0
- Latest-version selection mismatches: 0
- Public narratives present: 3,262 / 3,263 rows

後から提出された current-regime report version が古い incident を記述する場合があるため、incident date は 2025-06-16 より前になることがあります。Schema/reporting regime は incident date ではなく `source_regime` で識別します。

## 重要な解釈上の制限

Reporting entity や vehicle make の raw count は **crash rate ではなく safety ranking でもありません**。Reporting entity ごとに telemetry、crash awareness、fleet size、mileage/exposure、operating domain、reporting obligation が異なります。ADS と Level 2 ADAS でも reportability criteria が異なります。1 件の real-world crash に複数 reports が存在する場合があり、本プロジェクトは NHTSA の `Same Incident ID` を保持しますが、その field だけを使って report を自動統合しません。

## Source と rights

Source of truth は NHTSA Standing General Order on Crash Reporting です。Pipeline は NHTSA 公式 public CSV release のみを取り込み、同機関による PII/CBI redaction を保持します。一部の submitted narrative/content は reporting entity 由来のため、全 field に blanket public-domain claim を行わず、Kaggle license は保守的に `Other` としています。

詳細な rights/provenance gate は `research/source_rights.md`、regime decision は `research/pilot_decision.md` を参照してください。

## Rebuild

Windows では Python 3.12+ と UTF-8 I/O を使用します。

```powershell
$env:PYTHONUTF8='1'
$env:PYTHONIOENCODING='utf-8'
python -m pip install -r requirements.txt
python src\pipeline.py all
python src\build_product.py
python -m pytest -q
python -m ruff check .
```

各 stage は restartable で、個別に永続化されます。

```text
discover -> snapshot -> parse -> rights gate -> normalize -> QA -> manifest
```

Raw source snapshot は `data/raw/`、normalized intermediate は `data/derived/`、公開 data artifact は `release/data.csv`、詳細 research/QA/provenance は `research/`、`qa/`、`state/` に保存します。

## Research と QA

- `research/market_validation.md` — analog datasets, adoption evidence, pre-pilot scorecard
- `research/source_rights.md` — official-source discovery, regime semantics, redistribution basis
- `research/pilot_decision.md` — measured pilot, schema differences, re-score, V1 scope decision
- `qa/qa_report.json` — source-to-output reconciliation, versions, IDs, dates, missingness, narratives, anomalies
- `qa/column_mapping.json` — exact source-to-release column mapping と descriptions
- `qa/release_manifest.json` — generated release/source checksums と Git SHA。commit せず release ごとに再生成

## Showcase notebook

`notebooks/what-do-reported-autonomous-driving-crashes-look-like.ipynb` は公開 Kaggle notebook です。time trends、ADS/Level 2 categories、report/vehicle distributions、road/weather/crash characteristics、severity、narrative-text exploration を示しつつ、report count と safety rate を明確に区別します。
