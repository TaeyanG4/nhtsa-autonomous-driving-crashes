from __future__ import annotations

import json
from pathlib import Path

import nbformat as nbf
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "release"
NOTEBOOKS = ROOT / "notebooks"
MAPPING = ROOT / "qa" / "column_mapping.json"
DATASET_ID = "taeyangg4/nhtsa-autonomous-driving-crashes"
NOTEBOOK_ID = "taeyangg4/what-do-reported-autonomous-driving-crashes-look-like"


def write_json_no_bom(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def kaggle_type(name: str) -> str:
    explicit = {
        "report_id": "id",
        "report_version": "integer",
        "report_month": "integer",
        "report_year": "integer",
        "model_year": "integer",
        "latitude": "latitude",
        "longitude": "longitude",
        "address": "address",
        "city": "city",
        "state": "province",
        "zip_code": "postalcode",
        "sv_precrash_speed_mph": "numeric",
        "source_url": "url",
        "versions_observed_in_current_snapshot": "integer",
    }
    return explicit.get(name, "string")


def build_dataset_metadata() -> Path:
    mapping = json.loads(MAPPING.read_text(encoding="utf-8"))
    data = pd.read_csv(RELEASE / "data.csv", nrows=0, encoding="utf-8")
    fields = []
    by_name = {item["release_name"]: item for item in mapping}
    if list(data.columns) != [item["release_name"] for item in mapping]:
        raise RuntimeError("column mapping is not in exact release column order")
    for name in data.columns:
        fields.append(
            {
                "name": name,
                "description": by_name[name]["description"],
                "type": kaggle_type(name),
            }
        )

    description = """## About this dataset

Analysis-ready crash reports from the U.S. National Highway Traffic Safety Administration (NHTSA) Standing General Order on Crash Reporting.

This V1 deliberately covers the **current third-amended SGO reporting regime**, effective June 16, 2025. It combines NHTSA's current ADS, Level 2 ADAS, and Other/Unknown public incident files and keeps **one row per NHTSA Report ID**, selecting the highest available Report Version in the current source snapshot.

The current NHTSA release observed for this build contains incident reports through July 15, 2026. Some `incident_month` values are earlier than June 2025 because a report can be updated under the current regime for an older incident. Use `source_regime` and source provenance—not incident date alone—to identify the reporting regime.

### What is included

- vehicle make/model/year and the public VIN portion released by NHTSA
- automation category and engagement status
- incident month/time/location fields
- roadway, weather, crash counterpart, severity, tow/airbag/belt fields
- data-availability and investigation fields
- public incident narratives with NHTSA redactions preserved
- NHTSA identifiers including Report ID, Report Version, Same Incident ID, and Same Vehicle ID
- transparent source file, source URL, source bucket, and regime provenance

### Important limitations

**Raw report counts are not crash rates and must not be used as manufacturer/operator safety rankings.** NHTSA warns that reporting entities differ in telemetry, crash awareness, vehicle populations, operating locations, mileage/exposure, and other factors. ADS and Level 2 ADAS also have different reportability criteria. Initial reports may be incomplete or later updated, and the same real-world crash can have multiple reports.

`same_incident_id` is preserved as an NHTSA-provided linkage field but this dataset does not collapse suspected duplicate crashes. `report_submission_date` is the first submission month/year and is not used as a revision timestamp; latest-version selection uses the highest numeric `report_version` for each `report_id`.

### Source and redistribution basis

Source: NHTSA Standing General Order on Crash Reporting. NHTSA publishes these incident CSVs for public use after withholding/redacting personally identifiable information and information claimed as confidential business information. This derivative preserves those public-source redactions and does not add private or unredacted incident data. Because some submitted narrative/content originates with reporting entities, the Kaggle license is conservatively marked **Other** rather than making a blanket public-domain claim.

Reproducible build code, source snapshots/checksums, schema decisions, and detailed QA are maintained in the companion GitHub repository.
"""

    metadata = {
        "title": "Autonomous Driving Crash Reports — NHTSA",
        "subtitle": "Official ADS & Level 2 ADAS reports: vehicles, roads, severity & narratives",
        "description": description,
        "id": DATASET_ID,
        "licenses": [{"name": "other"}],
        "resources": [
            {
                "path": "data.csv",
                "description": (
                    "Canonical current-regime NHTSA SGO table: one row per Report ID using the highest available "
                    "Report Version. Includes ADS, Level 2 ADAS, Other/Unknown, public narratives, and explicit source provenance. "
                    "Counts are reports, not exposure-normalized crash rates."
                ),
                "schema": {"fields": fields},
            }
        ],
        "keywords": [
            "automotive",
            "transportation",
            "exploratory data analysis",
            "data visualization",
        ],
        "expectedUpdateFrequency": "monthly",
        "userSpecifiedSources": "NHTSA Standing General Order on Crash Reporting: https://www.nhtsa.gov/laws-regulations/standing-general-order-crash-reporting",
        "image": "dataset-cover-image.png",
    }
    path = RELEASE / "dataset-metadata.json"
    write_json_no_bom(path, metadata)
    return path


def build_notebook() -> tuple[Path, Path]:
    NOTEBOOKS.mkdir(parents=True, exist_ok=True)
    nb = nbf.v4.new_notebook()
    nb.metadata = {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3"},
    }
    cells = []
    cells.append(
        nbf.v4.new_markdown_cell(
            """# What Do Reported Autonomous-Driving Crashes Look Like?

This notebook is a fast visual tour of NHTSA's **reported** crashes involving Automated Driving Systems (ADS), Level 2 Advanced Driver Assistance Systems (ADAS), and the small Other/Unknown bucket in the current third-amended Standing General Order (SGO) data.

> **Interpretation guardrail:** counts below are counts of NHTSA reports, **not crash rates or safety rankings**. Reporting criteria, telemetry/awareness, vehicle fleets, mileage/exposure, operating domains, and update/duplicate behavior differ across reporting entities. The data do not provide the exposure denominator needed for manufacturer comparisons.

The dataset keeps one latest available Report Version per NHTSA Report ID. It does **not** merge rows merely because they share a Same Incident ID."""
        )
    )
    cells.append(
        nbf.v4.new_code_cell(
            """from pathlib import Path
from collections import Counter
import re

import matplotlib.pyplot as plt
import pandas as pd

pd.set_option('display.max_columns', 30)

candidates = [
    Path('/kaggle/input/nhtsa-autonomous-driving-crashes/data.csv'),
    Path('release/data.csv'),
    Path('../release/data.csv'),
]
DATA_PATH = next((p for p in candidates if p.exists()), None)
if DATA_PATH is None:
    raise FileNotFoundError('Could not find data.csv')

df = pd.read_csv(DATA_PATH, low_memory=False)
df['incident_month_dt'] = pd.to_datetime(df['incident_month'], format='%Y-%m', errors='coerce')
print(f'Loaded {len(df):,} latest-report rows and {df.shape[1]-1:,} release columns from {DATA_PATH}')"""
        )
    )
    cells.append(
        nbf.v4.new_markdown_cell(
            """## 1. Coverage and report structure

The current reporting regime starts June 16, 2025, but incident months can be older when a later/current-regime report version describes an earlier incident. We therefore keep `source_regime` explicit instead of inferring regime from `incident_month`."""
        )
    )
    cells.append(
        nbf.v4.new_code_cell(
            """same_counts = df.loc[df['same_incident_id'].fillna('').astype(str).str.strip().ne(''), 'same_incident_id'].value_counts()
summary = pd.Series({
    'latest Report IDs': df['report_id'].nunique(),
    'incident month min': df['incident_month_dt'].min().strftime('%Y-%m'),
    'incident month max': df['incident_month_dt'].max().strftime('%Y-%m'),
    'max selected Report Version': pd.to_numeric(df['report_version'], errors='coerce').max(),
    'rows with >1 current-snapshot version observed': (pd.to_numeric(df['versions_observed_in_current_snapshot']) > 1).sum(),
    'Same Incident IDs linking >1 output Report ID': (same_counts > 1).sum(),
})
display(summary.to_frame('value'))
display(df['source_bucket'].value_counts().rename_axis('source_bucket').to_frame('latest reports'))"""
        )
    )
    cells.append(
        nbf.v4.new_markdown_cell(
            """## 2. Reported incidents over time

This chart shows the month associated with each selected latest report. A changing line can reflect reporting scope, fleet activity, reporting behavior, source updates, or exposure—not only changes in crash risk."""
        )
    )
    cells.append(
        nbf.v4.new_code_cell(
            """monthly = (df.dropna(subset=['incident_month_dt'])
             .groupby(['incident_month_dt', 'source_bucket'])
             .size()
             .unstack(fill_value=0)
             .sort_index())
ax = monthly.plot(figsize=(12, 5), marker='o', linewidth=1.5)
ax.set_title('Latest NHTSA reports by incident month and source bucket')
ax.set_xlabel('Incident month')
ax.set_ylabel('Number of latest reports')
ax.legend(title='NHTSA source bucket')
plt.tight_layout()
plt.show()"""
        )
    )
    cells.append(
        nbf.v4.new_markdown_cell(
            """## 3. Reporting entities and vehicles

These are simple **report-count distributions**. They are useful for understanding who and what is represented in the file, but they are not comparable safety rates because fleet size, miles driven, operating domain, crash-detection capability, and reportability differ."""
        )
    )
    cells.append(
        nbf.v4.new_code_cell(
            """top_entities = df['reporting_entity'].value_counts().head(12).sort_values()
ax = top_entities.plot(kind='barh', figsize=(10, 6))
ax.set_title('Top reporting entities by number of latest reports — not a safety ranking')
ax.set_xlabel('Latest NHTSA reports')
ax.set_ylabel('Reporting entity')
plt.tight_layout()
plt.show()"""
        )
    )
    cells.append(
        nbf.v4.new_code_cell(
            """top_makes = df['make'].fillna('Unknown').replace('', 'Unknown').value_counts().head(12).sort_values()
ax = top_makes.plot(kind='barh', figsize=(10, 6))
ax.set_title('Vehicle makes appearing most often in latest reports — not a crash rate')
ax.set_xlabel('Latest NHTSA reports')
ax.set_ylabel('Vehicle make')
plt.tight_layout()
plt.show()"""
        )
    )
    cells.append(nbf.v4.new_markdown_cell("## 4. Roadway, weather, and crash characteristics"))
    cells.append(
        nbf.v4.new_code_cell(
            """roadway = df['roadway_type'].fillna('Unknown').replace('', 'Unknown').value_counts().head(10).sort_values()
ax = roadway.plot(kind='barh', figsize=(9, 5))
ax.set_title('Reported roadway type')
ax.set_xlabel('Latest reports')
plt.tight_layout()
plt.show()"""
        )
    )
    cells.append(
        nbf.v4.new_code_cell(
            """weather_cols = {
    'weather_clear': 'Clear',
    'weather_cloudy': 'Cloudy',
    'weather_partly_cloudy': 'Partly cloudy',
    'weather_rain': 'Rain',
    'weather_snow': 'Snow',
    'weather_fog_smoke_haze': 'Fog / smoke / haze',
    'weather_severe_wind': 'Severe wind',
    'weather_unk_see_narrative': 'Unknown / see narrative',
}
weather = pd.Series({label: df[col].fillna('').astype(str).str.strip().eq('Y').sum() for col, label in weather_cols.items()}).sort_values()
ax = weather.plot(kind='barh', figsize=(9, 5))
ax.set_title('Weather flags selected in latest reports')
ax.set_xlabel('Latest reports with flag = Y')
plt.tight_layout()
plt.show()"""
        )
    )
    cells.append(
        nbf.v4.new_code_cell(
            """crash_with = df['crash_with'].fillna('Unknown').replace('', 'Unknown').value_counts().head(12).sort_values()
ax = crash_with.plot(kind='barh', figsize=(9, 6))
ax.set_title('What the reported crash was with')
ax.set_xlabel('Latest reports')
plt.tight_layout()
plt.show()"""
        )
    )
    cells.append(nbf.v4.new_markdown_cell("## 5. Reported injury severity"))
    cells.append(
        nbf.v4.new_code_cell(
            """severity = df['highest_injury_severity_alleged'].fillna('Unknown').replace('', 'Unknown').value_counts().sort_values()
ax = severity.plot(kind='barh', figsize=(10, 6))
ax.set_title('Highest injury severity alleged in latest reports')
ax.set_xlabel('Latest reports')
plt.tight_layout()
plt.show()

display(severity.sort_values(ascending=False).to_frame('latest reports'))"""
        )
    )
    cells.append(
        nbf.v4.new_markdown_cell(
            """## 6. Narrative-text exploration

NHTSA's public narratives are highly useful for qualitative/text analysis. We keep the published text and its redactions. Rather than reproducing individual incident narratives here, the exploration below looks at text length and frequent words across the corpus."""
        )
    )
    cells.append(
        nbf.v4.new_code_cell(
            """narr = df['narrative'].fillna('').astype(str).str.strip()
lengths = narr[narr.ne('')].str.len()
print(f'Nonblank narratives: {len(lengths):,} / {len(df):,} ({len(lengths)/len(df):.1%})')
display(lengths.describe(percentiles=[.25, .5, .75, .9, .95]).to_frame('characters'))

ax = lengths.clip(upper=lengths.quantile(.99)).plot(kind='hist', bins=40, figsize=(10, 5))
ax.set_title('Narrative length distribution (x-axis clipped at 99th percentile)')
ax.set_xlabel('Characters')
plt.tight_layout()
plt.show()"""
        )
    )
    cells.append(
        nbf.v4.new_code_cell(
            """stop = set('''the a an and or but if then of to in on at for from by with without as is are was were be been being this that these those it its vehicle vehicles crash incident report reported reporting driver road roadway system automation ads adas nhtsa unknown see narrative subject other into after before during about approximately'''.split())
tokens = []
for text in narr[narr.ne('')]:
    words = re.findall(r"[A-Za-z][A-Za-z'-]{2,}", text.lower())
    tokens.extend(w for w in words if w not in stop)

common = pd.Series(dict(Counter(tokens).most_common(25))).sort_values()
ax = common.plot(kind='barh', figsize=(10, 8))
ax.set_title('Frequent words in public incident narratives')
ax.set_xlabel('Token count')
plt.tight_layout()
plt.show()"""
        )
    )
    cells.append(
        nbf.v4.new_markdown_cell(
            """## What this dataset cannot tell us

- It does not contain a consistent denominator such as miles driven, vehicle population, or operating-domain exposure.
- Reporting entities have different data access and crash-awareness capabilities.
- ADS and Level 2 ADAS reporting criteria differ.
- A real-world crash can produce multiple reports; `same_incident_id` is useful linkage evidence but is not perfect and is not used here to silently deduplicate.
- Reports can be revised. This dataset selects the highest currently available `report_version` for each `report_id`.
- The third-amended SGO changed reporting scope/fields beginning June 16, 2025. This V1 intentionally avoids forcing the older schema into the current one.

Use these data to describe **reported crash records and their characteristics**, not to infer relative manufacturer safety without appropriate external exposure and study design."""
        )
    )

    nb.cells = cells
    nb_path = NOTEBOOKS / "what-do-reported-autonomous-driving-crashes-look-like.ipynb"
    nbf.write(nb, nb_path)

    kernel_meta = {
        "id": NOTEBOOK_ID,
        "title": "What Do Reported Autonomous-Driving Crashes Look Like?",
        "code_file": nb_path.name,
        "language": "python",
        "kernel_type": "notebook",
        "is_private": "false",
        "enable_gpu": "false",
        "enable_tpu": "false",
        "enable_internet": "false",
        "machine_shape": "",
        "dataset_sources": [DATASET_ID],
        "competition_sources": [],
        "kernel_sources": [],
        "model_sources": [],
    }
    meta_path = NOTEBOOKS / "kernel-metadata.json"
    write_json_no_bom(meta_path, kernel_meta)
    return nb_path, meta_path


def main() -> None:
    metadata = build_dataset_metadata()
    notebook, kernel_meta = build_notebook()
    print(metadata.relative_to(ROOT))
    print(notebook.relative_to(ROOT))
    print(kernel_meta.relative_to(ROOT))


if __name__ == "__main__":
    main()
