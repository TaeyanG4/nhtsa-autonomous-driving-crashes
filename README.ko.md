# 자율주행 충돌 보고서 — NHTSA

[English](README.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | [简体中文](README.zh-CN.md)

ADS, Level 2 ADAS 및 Other/Unknown 보고서를 대상으로 하는 **현재의 세 번째 개정 NHTSA Standing General Order(SGO) 충돌 보고 체계**를 재현 가능하게 Kaggle에 배포하는 프로젝트입니다.

## 라이브 릴리스

- Kaggle 데이터셋: https://www.kaggle.com/datasets/taeyangg4/nhtsa-autonomous-driving-crashes
- 쇼케이스 노트북: https://www.kaggle.com/code/taeyangg4/what-do-reported-self-driving-crashes-look-like

Kaggle 노트북 카드에는 플랫폼 제목 길이 제한을 맞추기 위해 더 짧은 **“What Do Reported Self-Driving Crashes Look Like?”**를 사용합니다. 노트북 본문의 H1에는 의도한 긴 제목 **“What Do Reported Autonomous-Driving Crashes Look Like?”**를 그대로 유지합니다.

## 릴리스 설계

공개 Kaggle 제품은 의도적으로 단순하게 `data.csv` 하나만 제공합니다. 각 행은 NHTSA `Report ID` 하나이며, 현재 NHTSA 원본 파일에서 사용 가능한 가장 높은 숫자의 `Report Version`을 선택합니다. 현재 원본의 116개 필드를 모두 snake_case로 보존하고, 출처 추적과 편의를 위한 7개 컬럼을 추가합니다.

V1은 2021년부터 2025년 6월까지의 아카이브를 현재 스키마에 강제로 맞추지 않습니다. 파일럿에서 현재 스키마는 116개 컬럼, 아카이브는 137개 컬럼이었고 이름이 공통인 컬럼은 89개뿐이었으며 여러 핵심 개념과 관측 단위가 달랐습니다. 역사 데이터 조화는 명확한 사용자 가치와 방어 가능한 매핑이 있을 때까지 미룹니다.

## 현재 측정된 릴리스

- 원본 스냅샷 ID: `20260827`
- 현재 원본 버전 행 수: 3,413
- 정규화된 최신 Report ID 수: 3,263
- 컬럼 수: 123
- 선택된 행의 incident month 범위: 2023-01 ~ 2026-07
- 현재 체계 report submission 범위: 2025-06 ~ 2026-07
- 중복 `(Report ID, Report Version)` 원본 쌍: 0
- 최신 버전 선택 불일치: 0
- 공개 narrative 존재: 3,262 / 3,263행

사고 날짜가 2025년 6월 16일보다 이를 수 있는 이유는 현재 체계에서 제출된 후속/최신 보고 버전이 더 오래된 사고를 설명할 수 있기 때문입니다. 스키마/보고 체계는 사고 날짜가 아니라 `source_regime`으로 식별해야 합니다.

## 중요한 해석 제한

보고 주체나 차량 제조사별 단순 건수는 **충돌률이 아니며 안전 순위도 아닙니다**. 보고 주체마다 텔레메트리, 충돌 인지 능력, 운행 차량 수, 주행거리/노출, 운행 영역, 보고 의무가 다릅니다. ADS와 Level 2 ADAS의 보고 기준도 서로 다릅니다. 하나의 실제 충돌이 여러 보고서로 이어질 수 있으므로 이 프로젝트는 NHTSA의 `Same Incident ID`를 보존하지만 이 필드만으로 보고서를 묵시적으로 병합하지 않습니다.

## 원본과 권리

원본 기준은 NHTSA Standing General Order on Crash Reporting입니다. 파이프라인은 NHTSA의 공식 공개 CSV만 수집하고 기관이 적용한 PII/CBI 비공개·삭제 처리를 그대로 보존합니다. 일부 narrative/내용의 원저작자가 보고 주체일 수 있으므로 Kaggle 라이선스는 보수적으로 `Other`로 설정하며 모든 필드를 포괄적으로 퍼블릭 도메인이라고 주장하지 않습니다.

전체 권리/출처 게이트는 `research/source_rights.md`, 보고 체계 결정은 `research/pilot_decision.md`를 참고하세요.

## 재빌드

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

각 단계는 재시작 가능하며 별도로 상태를 저장합니다.

```text
discover -> snapshot -> parse -> rights gate -> normalize -> QA -> manifest
```

원본 스냅샷은 `data/raw/`, 정규화 중간 산출물은 `data/derived/`, 공개 데이터 산출물은 `release/data.csv`, 상세 조사·QA·출처 정보는 `research/`, `qa/`, `state/`에 위치합니다.

## 조사 및 QA

- `research/market_validation.md` — 유사 데이터셋, 채택 근거, 파일럿 이전 점수표
- `research/source_rights.md` — 공식 원본 탐색, 보고 체계 의미, 재배포 근거
- `research/pilot_decision.md` — 측정된 파일럿, 스키마 차이, 재평가, V1 범위 결정
- `qa/qa_report.json` — 원본-출력 대조, 버전, ID, 날짜, 결측, narrative, 이상치
- `qa/column_mapping.json` — 정확한 원본-릴리스 컬럼 매핑과 설명
- `qa/release_manifest.json` — 생성된 릴리스/원본 체크섬과 Git SHA(커밋하지 않으며 릴리스마다 재생성)

## 쇼케이스 노트북

`notebooks/what-do-reported-autonomous-driving-crashes-look-like.ipynb`는 공개 Kaggle 노트북입니다. 시간 추세, ADS/Level 2 범주, 보고/차량 분포, 도로·날씨·충돌 특성, 중상도, narrative 텍스트 탐색을 보여주며 보고 건수와 안전률이 다르다는 점을 반복해서 명시합니다.
