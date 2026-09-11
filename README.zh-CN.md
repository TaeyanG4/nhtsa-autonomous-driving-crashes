# Autonomous Driving Crash Reports — NHTSA

[English](README.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | **简体中文**

这是一个面向 Kaggle 的可复现项目，整理 **current third-amended NHTSA Standing General Order (SGO) crash-reporting regime** 中的 ADS、Level 2 ADAS 与 Other/Unknown reports。

## Release 设计

公开 Kaggle 产品刻意保持简单，仅提供一个 `data.csv`。每行对应一个 NHTSA `Report ID`，并选择 current NHTSA source files 中可用的最高数值 `Report Version`。Current source 的 116 个字段全部以 snake_case 保留，并增加 7 个透明的 provenance/convenience columns。

V1 不会强行把 2021 年至 2025 年 6 月 archive 合并进 current schema。Pilot 发现 current 有 116 columns、archive 有 137 columns，仅 89 个名称相同，并存在多处重要的 concept/grain 差异。Historical harmonization 将推迟到存在明确 user benefit 和可辩护 mapping 时再做。

## 当前实测 Release

- Source snapshot ID: `20260827`
- Current source version rows: 3,413
- Canonical latest Report IDs: 3,263
- Columns: 123
- 所选行 incident month coverage: 2023-01 至 2026-07
- current-regime report submission coverage: 2025-06 至 2026-07
- Duplicate `(Report ID, Report Version)` source pairs: 0
- Latest-version selection mismatches: 0
- Public narratives present: 3,262 / 3,263 rows

较晚提交的 current-regime report version 可能描述更早发生的 incident，因此 incident date 可能早于 2025-06-16。Schema/reporting regime 应通过 `source_regime` 判断，而不是仅看 incident date。

## 重要解释限制

Reporting entity 或 vehicle make 的 raw count **不是 crash rate，也不是 safety ranking**。不同 reporting entity 在 telemetry、crash awareness、fleet size、mileage/exposure、operating domain 与 reporting obligation 上存在差异。ADS 与 Level 2 ADAS 的 reportability criteria 也不同。一个 real-world crash 可能存在多个 reports；本项目保留 NHTSA 的 `Same Incident ID`，但不会仅凭该字段静默合并 reports。

## Source 与 rights

Source of truth 是 NHTSA Standing General Order on Crash Reporting。Pipeline 仅采集 NHTSA 官方公开 CSV release，并保留机构已有的 PII/CBI redaction。部分 submitted narrative/content 来自 reporting entity，因此本项目不会对所有字段作 blanket public-domain claim，Kaggle license 保守标记为 `Other`。

完整 rights/provenance gate 见 `research/source_rights.md`，regime decision 见 `research/pilot_decision.md`。

## Rebuild

在 Windows 上使用 Python 3.12+ 与 UTF-8 I/O：

```powershell
$env:PYTHONUTF8='1'
$env:PYTHONIOENCODING='utf-8'
python -m pip install -r requirements.txt
python src\pipeline.py all
python src\build_product.py
python -m pytest -q
python -m ruff check .
```

各 stage 可重启，并分别持久化：

```text
discover -> snapshot -> parse -> rights gate -> normalize -> QA -> manifest
```

Raw source snapshots 位于 `data/raw/`，normalized intermediates 位于 `data/derived/`，唯一公开 data artifact 位于 `release/data.csv`，详细 research/QA/provenance 位于 `research/`、`qa/` 与 `state/`。

## Research 与 QA

- `research/market_validation.md` — analog datasets、adoption evidence、pre-pilot scorecard
- `research/source_rights.md` — official-source discovery、regime semantics、redistribution basis
- `research/pilot_decision.md` — measured pilot、schema differences、re-score、V1 scope decision
- `qa/qa_report.json` — source-to-output reconciliation、versions、IDs、dates、missingness、narratives、anomalies
- `qa/column_mapping.json` — exact source-to-release column mapping 与 descriptions
- `qa/release_manifest.json` — generated release/source checksums 与 Git SHA；不 commit，每次 release 重新生成

## Showcase notebook

`notebooks/what-do-reported-autonomous-driving-crashes-look-like.ipynb` 是公开 Kaggle notebook。它展示 time trends、ADS/Level 2 categories、report/vehicle distributions、road/weather/crash characteristics、severity 与 narrative-text exploration，同时持续明确区分 report count 和 safety rate。
