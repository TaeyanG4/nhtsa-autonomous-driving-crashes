# 自動運転クラッシュ報告 — NHTSA

[English](README.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | [简体中文](README.zh-CN.md)

ADS、Level 2 ADAS、Other/Unknown の報告を対象とする、**現在の第3次改訂 NHTSA Standing General Order（SGO）クラッシュ報告制度**を再現可能な形で Kaggle に公開するプロジェクトです。

## ライブリリース

- Kaggle データセット: https://www.kaggle.com/datasets/taeyangg4/nhtsa-autonomous-driving-crashes
- ショーケースノートブック: https://www.kaggle.com/code/taeyangg4/what-do-reported-self-driving-crashes-look-like
- Kaggle version / status: `1 / Ready`
- Kaggle Usability: `10.0 / 10`
- Data Explorer metadata: `data.csv` description `1/1` exact、column descriptions `123/123` exact

Kaggle のノートブックカードではタイトル長の制約に合わせて **“What Do Reported Self-Driving Crashes Look Like?”** を使用しています。ノートブック本文の H1 には、意図した長いタイトル **“What Do Reported Autonomous-Driving Crashes Look Like?”** をそのまま保持しています。

## リリース設計

公開 Kaggle 製品は意図的に単純化し、`data.csv` 1ファイルのみです。各行は NHTSA の `Report ID` 1件で、現在の NHTSA ソースファイルで利用可能な最大の数値 `Report Version` を採用します。現在の116個のソースフィールドをすべて snake_case で保持し、来歴・利便性のための7列を追加しています。

V1 は 2021年から2025年6月までのアーカイブを現在スキーマへ無理に統合しません。パイロットでは現在スキーマ116列、アーカイブ137列で、共通名は89列のみ、複数の重要な概念・粒度変更が確認されました。履歴統合は、明確な利用価値と防御可能なマッピングが得られるまで延期します。

## 現在の測定済みリリース

- ソーススナップショット ID: `20260827`
- 現在ソースのバージョン行数: 3,413
- 正規化された最新 Report ID: 3,263
- 列数: 123
- 選択行の incident month 範囲: 2023-01 ～ 2026-07
- 現行制度の report submission 範囲: 2025-06 ～ 2026-07
- 重複 `(Report ID, Report Version)` ソースペア: 0
- 最新バージョン選択の不一致: 0
- 公開 narrative あり: 3,262 / 3,263 行

事故日が2025年6月16日より前になる場合があります。現行制度下で提出された後続・最新バージョンが古い事故を記述できるためです。スキーマ／報告制度は事故日ではなく `source_regime` で判定してください。

## 重要な解釈上の制限

報告主体や車両メーカーごとの単純件数は **クラッシュ率ではなく、安全性ランキングでもありません**。報告主体ごとにテレメトリ、事故把握能力、車両数、走行距離／曝露、運行領域、報告義務が異なります。ADS と Level 2 ADAS では報告基準も異なります。1件の実事故から複数の報告が生じる場合があるため、本プロジェクトは NHTSA の `Same Incident ID` を保持しますが、この値だけで報告を暗黙に統合しません。

## ソースと権利

基準ソースは NHTSA Standing General Order on Crash Reporting です。パイプラインは NHTSA の公式公開 CSV のみを取り込み、当局が適用した PII/CBI の非公開・墨消しを保持します。一部の narrative／内容は報告主体に由来するため、Kaggle のライセンスは保守的に `Other` とし、すべてのフィールドが包括的にパブリックドメインであるとは主張しません。

詳細な権利・来歴ゲートは `research/source_rights.md`、制度判断は `research/pilot_decision.md` を参照してください。

## 再ビルド

Windows 上の Python 3.12+ と UTF-8 I/O を使用します。

```powershell
$env:PYTHONUTF8='1'
$env:PYTHONIOENCODING='utf-8'
python -m pip install -r requirements.txt
python src\pipeline.py all
python src\build_product.py
python -m pytest -q
python -m ruff check .
```

各ステージは再開可能で、状態は別々に保存されます。

```text
discover -> snapshot -> parse -> rights gate -> normalize -> QA -> manifest
```

生ソーススナップショットは `data/raw/`、正規化中間データは `data/derived/`、公開データ成果物は `release/data.csv`、詳細な調査・QA・来歴は `research/`、`qa/`、`state/` にあります。

## 調査と QA

- `research/market_validation.md` — 類似データセット、採用根拠、パイロット前スコアカード
- `research/source_rights.md` — 公式ソース探索、制度の意味、再配布根拠
- `research/pilot_decision.md` — 測定パイロット、スキーマ差、再評価、V1 範囲決定
- `qa/qa_report.json` — ソース対出力の照合、バージョン、ID、日付、欠損、narrative、異常
- `qa/column_mapping.json` — 正確なソース→リリース列マッピングと説明
- `qa/release_manifest.json` — 生成済みリリース／ソースチェックサムと Git SHA（コミットせず、リリースごとに再生成）

## ショーケースノートブック

`notebooks/what-do-reported-autonomous-driving-crashes-look-like.ipynb` は公開 Kaggle ノートブックです。時系列傾向、ADS/Level 2 カテゴリ、報告／車両分布、道路・天候・衝突特性、傷害重症度、narrative テキスト探索を示し、報告件数と安全率を区別する注意を繰り返し明記しています。
