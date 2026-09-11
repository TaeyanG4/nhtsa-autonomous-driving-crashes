# 自动驾驶碰撞报告 — NHTSA

[English](README.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | [简体中文](README.zh-CN.md)

这是一个可复现的 Kaggle 发布项目，覆盖 ADS、Level 2 ADAS 与 Other/Unknown 报告，范围限定为**当前第三次修订后的 NHTSA Standing General Order（SGO）碰撞报告制度**。

## 在线发布

- Kaggle 数据集: https://www.kaggle.com/datasets/taeyangg4/nhtsa-autonomous-driving-crashes
- 展示 Notebook: https://www.kaggle.com/code/taeyangg4/what-do-reported-self-driving-crashes-look-like
- Kaggle version / status: `1 / Ready`
- Kaggle Usability: `10.0 / 10`
- Data Explorer metadata: `data.csv` description `1/1` exact，column descriptions `123/123` exact

为满足 Kaggle 的标题长度限制，Notebook 卡片使用较短标题 **“What Do Reported Self-Driving Crashes Look Like?”**。Notebook 正文 H1 仍保留预期的完整标题 **“What Do Reported Autonomous-Driving Crashes Look Like?”**。

## 发布设计

公开 Kaggle 产品刻意保持简单：只有一个 `data.csv`。每一行对应一个 NHTSA `Report ID`，并选取当前 NHTSA 源文件中该 ID 可用的最高数值 `Report Version`。当前源数据的116个字段全部以 snake_case 保留，并增加7个透明的来源追踪/便利字段。

V1 不会强行把 2021 年至 2025 年 6 月的历史归档映射到当前模式。试点发现当前模式有116列、归档模式有137列，仅89个列名相同，而且若干关键概念和数据粒度发生了实质变化。历史统一将在存在明确用户价值和可辩护映射后再考虑。

## 当前实测发布

- 源快照 ID: `20260827`
- 当前源版本记录行数: 3,413
- 规范化后的最新 Report ID: 3,263
- 列数: 123
- 所选记录的 incident month 范围: 2023-01 至 2026-07
- 当前制度的 report submission 范围: 2025-06 至 2026-07
- 重复 `(Report ID, Report Version)` 源记录对: 0
- 最新版本选择不一致: 0
- 有公开 narrative 的记录: 3,262 / 3,263

事故日期可能早于 2025 年 6 月 16 日，因为在当前制度下提交的后续/最新版本可以描述更早发生的事故。应使用 `source_regime`，而不是仅凭事故日期，来识别模式/报告制度。

## 重要解释限制

按报告主体或汽车品牌统计的原始数量**不是碰撞率，也不是安全排名**。不同报告主体在遥测能力、事故获知能力、车辆规模、里程/暴露、运营区域和报告义务方面都不同。ADS 与 Level 2 ADAS 的可报告标准也不同。一次现实世界碰撞可能产生多份报告；本项目保留 NHTSA 的 `Same Incident ID`，但不会仅依据该字段静默合并报告。

## 来源与权利

权威来源是 NHTSA Standing General Order on Crash Reporting。流水线仅摄取 NHTSA 官方公开 CSV，并保留该机构对 PII/CBI 的隐藏与删节。由于部分 narrative/内容最初由报告主体提供，Kaggle 许可证保守设置为 `Other`，本项目不会声称所有字段都属于公共领域。

完整权利/来源门控见 `research/source_rights.md`，制度范围决策见 `research/pilot_decision.md`。

## 重建

在 Windows 上使用 Python 3.12+ 和 UTF-8 I/O：

```powershell
$env:PYTHONUTF8='1'
$env:PYTHONIOENCODING='utf-8'
python -m pip install -r requirements.txt
python src\pipeline.py all
python src\build_product.py
python -m pytest -q
python -m ruff check .
```

各阶段均可恢复执行，并分别持久化状态：

```text
discover -> snapshot -> parse -> rights gate -> normalize -> QA -> manifest
```

原始源快照位于 `data/raw/`，规范化中间产物位于 `data/derived/`，唯一的公开数据产物位于 `release/data.csv`，详细研究、QA 与来源信息位于 `research/`、`qa/` 和 `state/`。

## 研究与 QA

- `research/market_validation.md` — 类似数据集、采用证据、试点前评分卡
- `research/source_rights.md` — 官方源发现、制度语义、再分发依据
- `research/pilot_decision.md` — 实测试点、模式差异、重新评分、V1 范围决策
- `qa/qa_report.json` — 源到输出对账、版本、ID、日期、缺失、narrative、异常
- `qa/column_mapping.json` — 精确的源到发布列映射及说明
- `qa/release_manifest.json` — 生成的发布/源校验和与 Git SHA（不提交；每次发布重新生成）

## 展示 Notebook

`notebooks/what-do-reported-autonomous-driving-crashes-look-like.ipynb` 是公开 Kaggle Notebook。它展示时间趋势、ADS/Level 2 类别、报告/车辆分布、道路/天气/碰撞特征、伤害严重度和 narrative 文本探索，并反复强调报告数量不等于安全率。
