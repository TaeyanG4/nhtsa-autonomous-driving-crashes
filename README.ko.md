# Autonomous Driving Crash Reports — NHTSA

[English](README.md) | **한국어** | [日本語](README.ja.md) | [简体中文](README.zh-CN.md)

ADS, Level 2 ADAS, Other/Unknown 보고를 포함하는 **현행 third-amended NHTSA Standing General Order(SGO) 충돌사고 보고 체계**를 재현 가능하게 Kaggle용으로 구축하는 프로젝트입니다.

## Release 설계

공개 Kaggle 제품은 의도적으로 단순하게 `data.csv` 하나만 제공합니다. 각 행은 하나의 NHTSA `Report ID`이며, 현행 NHTSA 원본에서 사용 가능한 가장 높은 숫자형 `Report Version`을 선택합니다. 현재 원본 116개 필드를 snake_case로 모두 보존하고, provenance/편의용 투명한 파생 컬럼 7개를 추가합니다.

V1은 2021년~2025년 6월 archive를 현행 schema에 억지로 합치지 않습니다. Pilot에서 현행 116컬럼, archive 137컬럼, 공통 이름 89개만 확인됐고 concept/grain 차이도 여러 개 존재했습니다. Historical harmonization은 명확한 사용자 가치와 방어 가능한 mapping이 생길 때까지 보류합니다.

## 현재 실측 Release

- Source snapshot ID: `20260827`
- Current source version rows: 3,413
- Canonical latest Report IDs: 3,263
- Columns: 123
- 선택 행 incident month 범위: 2023-01 ~ 2026-07
- 현행 regime report submission 범위: 2025-06 ~ 2026-07
- 중복 `(Report ID, Report Version)` source pairs: 0
- Latest-version selection mismatches: 0
- Public narratives present: 3,262 / 3,263 rows

나중에 제출된 현행 regime report version이 더 오래된 사고를 기술할 수 있으므로 incident date는 2025-06-16보다 이를 수 있습니다. Schema/reporting regime은 incident date가 아니라 `source_regime`으로 구분합니다.

## 중요한 해석 제한

Reporting entity 또는 vehicle make의 raw count는 **crash rate가 아니며 safety ranking도 아닙니다**. Reporting entity마다 telemetry, crash awareness, fleet size, mileage/exposure, operating domain, reporting obligation이 다릅니다. ADS와 Level 2 ADAS도 reportability 기준이 다릅니다. 하나의 실제 사고에 여러 report가 있을 수 있으며, 본 프로젝트는 NHTSA의 `Same Incident ID`를 보존하지만 이 필드만으로 report를 자동 병합하지 않습니다.

## Source 및 권리

Source of truth는 NHTSA Standing General Order on Crash Reporting입니다. Pipeline은 NHTSA 공식 공개 CSV만 수집하며 기관이 적용한 PII/CBI redaction을 그대로 보존합니다. 일부 제출 narrative/content는 reporting entity에서 유래하므로 모든 필드를 포괄적으로 public domain이라고 주장하지 않고 Kaggle license는 보수적으로 `Other`로 표시합니다.

전체 rights/provenance gate는 `research/source_rights.md`, regime 결정은 `research/pilot_decision.md`를 참고합니다.

## Rebuild

Windows에서 Python 3.12+와 UTF-8 I/O를 사용합니다.

```powershell
$env:PYTHONUTF8='1'
$env:PYTHONIOENCODING='utf-8'
python -m pip install -r requirements.txt
python src\pipeline.py all
python src\build_product.py
python -m pytest -q
python -m ruff check .
```

Stage는 재시작 가능하며 각각 분리 저장됩니다.

```text
discover -> snapshot -> parse -> rights gate -> normalize -> QA -> manifest
```

원본 snapshot은 `data/raw/`, normalized intermediate는 `data/derived/`, 공개 데이터는 `release/data.csv`, 상세 research/QA/provenance는 `research/`, `qa/`, `state/`에 둡니다.

## Research 및 QA

- `research/market_validation.md` — analog datasets, adoption evidence, pre-pilot scorecard
- `research/source_rights.md` — official-source discovery, regime semantics, redistribution basis
- `research/pilot_decision.md` — measured pilot, schema differences, re-score, V1 scope decision
- `qa/qa_report.json` — source-to-output reconciliation, versions, IDs, dates, missingness, narratives, anomalies
- `qa/column_mapping.json` — source-to-release column mapping과 description
- `qa/release_manifest.json` — release/source checksum과 Git SHA; commit하지 않고 release마다 재생성

## Showcase notebook

`notebooks/what-do-reported-autonomous-driving-crashes-look-like.ipynb`는 공개 Kaggle notebook입니다. 시간 추세, ADS/Level 2 category, report/vehicle 분포, road/weather/crash 특성, severity, narrative text를 탐색하면서 report count와 safety rate를 반복해서 구분합니다.
