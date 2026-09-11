# Phase 1 - Market validation

Observed: 2026-09-11. Metrics were collected from the live Kaggle API/CLI search results and are point-in-time values.

## Product test

- **Title:** Autonomous Driving Crash Reports — NHTSA
- **Subtitle:** Official ADS & Level 2 ADAS crash reports with vehicles, road conditions, severity and incident narratives
- **Target user:** Kaggle users doing transportation-safety EDA, data visualization, text exploration, or reproducible public-data analysis.
- **Primary task/question:** What do reported ADS and Level 2 ADAS crashes look like across time, system category, vehicle, roadway/weather, crash characteristics, severity, and narrative text?
- **First notebook:** “What Do Reported Autonomous-Driving Crashes Look Like?”
- **Five-minute experience:** open one CSV; parse incident month; group by automation category / vehicle / roadway / severity; inspect narratives without joining tables.
- **Release shape:** one public `data.csv`; source snapshots, QA, mappings, and manifests stay in GitHub.
- **Closest alternative:** `darkmatternet/automated-driving-crash-reports` — 6 votes, 89 downloads, 295 views after 25 days, about 4.2 MB reported dataset size. Its public root has 10 artifacts including duplicate CSV/Parquet representations, both history/latest tables, summaries, dictionary, QA, and manifest.
- **Why choose this instead:** deliberately lower activation friction (one canonical file), explicit third-amended-SGO regime semantics, source-faithful latest-version logic, stronger field descriptions/provenance, and a focused public notebook that does not turn raw manufacturer report counts into safety rankings.

## Adoption evidence

The broad road-crash niche is proven: several accident datasets have thousands to hundreds of thousands of downloads, hundreds to thousands of votes, and substantial notebook reuse. NHTSA-origin fatality datasets also show strong reuse. The direct SGO niche is much smaller, but the closest direct alternative reached 89 downloads and 6 votes in only 25 days, which is enough to justify a small pilot rather than a large historical build.

The analog detail is in `market_analogs.csv`. Adoption reasons are inferences from visible usage metrics, task fit, file size, freshness, and notebook reuse—not statements from the dataset owners.

## Pre-pilot scorecard

| Dimension | Score / 5 | Weighted points | Rationale |
|---|---:|---:|---|
| Proven demand / adoption evidence | 4 | 12/15 | Strong crash-data demand; direct SGO demand is early but non-zero |
| Distinctiveness / moat | 3 | 9/15 | A near-direct SGO alternative already exists |
| Clear task / first insight | 5 | 10/10 | Time, vehicle, conditions, severity, text are immediately analyzable |
| Global or broad audience reach | 4 | 8/10 | US source, but autonomous-driving safety has broad interest |
| Time-to-first-insight | 5 | 10/10 | Single-table target and ordinary CPU/RAM |
| Source authority + rights clarity | 4 | 8/10 | Official NHTSA public files; redistribution wording still needs explicit gate |
| Freshness / update value | 5 | 5/5 | NHTSA states monthly updates |
| Collection + rebuild efficiency | 5 | 5/5 | Small official CSV downloads, no crawl needed |
| Download/runtime friction | 5 | 5/5 | Expected release is only a few MB |
| Portfolio diversification | 4 | 4/5 | Public-safety + autonomous-driving + narrative modality |
| Notebook/visual hook strength | 5 | 10/10 | Time/category/conditions/severity/text all visualize well |
| **Total** |  | **86/100** |  |

## Decision

**PILOT.** The score is high enough to continue, but the closest direct alternative is recent and materially similar. A historical harmonization effort is not justified until the official-source pilot proves that a cleaner V1 can be both simpler and semantically safer.
