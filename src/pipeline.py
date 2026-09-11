from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "state" / "source_catalog.json"
STATE = ROOT / "state"
RAW = ROOT / "data" / "raw" / "snapshots"
DERIVED = ROOT / "data" / "derived"
RELEASE = ROOT / "release"
QA = ROOT / "qa"

CURRENT_KEYS = ("current_ads", "current_adas", "current_other")
CURRENT_DOC_KEYS = ("current_dictionary",)
SOURCE_PAGE = "https://www.nhtsa.gov/laws-regulations/standing-general-order-crash-reporting"
REGIME = "third_amended_sgo_effective_2025-06-16"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(obj, indent=2, ensure_ascii=False) + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_catalog() -> dict[str, Any]:
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    if catalog.get("source_page") != SOURCE_PAGE:
        raise RuntimeError("source catalog does not point at the required NHTSA SGO source-of-truth page")
    observed = datetime.fromisoformat(catalog["observed_at"])
    age_days = (datetime.now(timezone.utc) - observed.astimezone(timezone.utc)).total_seconds() / 86400
    if age_days > 45:
        raise RuntimeError(
            f"source catalog is {age_days:.1f} days old; refresh it from the live NHTSA SGO page before rebuild"
        )
    return catalog


def source_by_key(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {x["key"]: x for x in catalog["sources"]}


def head(url: str) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        method="HEAD",
        headers={"User-Agent": "Mozilla/5.0 NHTSA-Kaggle-Dataset/1.0"},
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            headers = response.headers
            return {
                "ok": True,
                "status": int(response.status),
                "content_type": headers.get("Content-Type"),
                "content_length": headers.get("Content-Length"),
                "last_modified": headers.get("Last-Modified"),
                "etag": headers.get("ETag"),
                "seconds": round(time.perf_counter() - started, 3),
            }
    except urllib.error.HTTPError as exc:
        return {
            "ok": False,
            "status": int(exc.code),
            "error": str(exc),
            "seconds": round(time.perf_counter() - started, 3),
        }


def stage_discover() -> dict[str, Any]:
    catalog = load_catalog()
    by_key = source_by_key(catalog)
    checks = []
    for key in (*CURRENT_KEYS, *CURRENT_DOC_KEYS):
        src = by_key[key]
        check = head(src["url"])
        checks.append({"key": key, "url": src["url"], **check})
        if not check["ok"]:
            raise RuntimeError(f"official source verification failed for {key}: {check}")
    result = {
        "generated_at": now_iso(),
        "source_page": SOURCE_PAGE,
        "catalog_observed_at": catalog["observed_at"],
        "page_observed_data_through": catalog.get("page_observed_data_through"),
        "note": (
            "The NHTSA HTML page is protected by an anti-bot layer from this Windows host. "
            "The source catalog was refreshed from the live page in-session; this stage verifies every official static source URL before use."
        ),
        "checks": checks,
    }
    write_json(STATE / "discovery.json", result)
    return result


def download(url: str, target: Path) -> dict[str, Any]:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.stat().st_size > 0:
        return {
            "downloaded": False,
            "bytes": target.stat().st_size,
            "sha256": sha256(target),
        }
    tmp = target.with_suffix(target.suffix + ".part")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 NHTSA-Kaggle-Dataset/1.0"})
    started = time.perf_counter()
    with urllib.request.urlopen(req, timeout=120) as response, tmp.open("wb") as out:
        while True:
            block = response.read(1024 * 1024)
            if not block:
                break
            out.write(block)
    tmp.replace(target)
    return {
        "downloaded": True,
        "bytes": target.stat().st_size,
        "sha256": sha256(target),
        "seconds": round(time.perf_counter() - started, 3),
    }


def snapshot_id_from_discovery(discovery: dict[str, Any]) -> str:
    # Use the latest source Last-Modified date so rebuilds on unchanged upstream files
    # reuse the same deterministic snapshot folder.
    dates = []
    for check in discovery["checks"]:
        value = check.get("last_modified")
        if value:
            try:
                dates.append(datetime.strptime(value, "%a, %d %b %Y %H:%M:%S %Z"))
            except ValueError:
                pass
    if dates:
        return max(dates).strftime("%Y%m%d")
    return datetime.now(timezone.utc).strftime("%Y%m%d")


def stage_snapshot() -> dict[str, Any]:
    discovery_path = STATE / "discovery.json"
    discovery = json.loads(discovery_path.read_text(encoding="utf-8")) if discovery_path.exists() else stage_discover()
    catalog = load_catalog()
    by_key = source_by_key(catalog)
    snapshot_id = snapshot_id_from_discovery(discovery)
    folder = RAW / snapshot_id
    files = []
    for key in (*CURRENT_KEYS, *CURRENT_DOC_KEYS):
        src = by_key[key]
        filename = src["url"].rsplit("/", 1)[-1]
        target = folder / filename
        info = download(src["url"], target)
        files.append(
            {
                "key": key,
                "bucket": src.get("bucket"),
                "url": src["url"],
                "path": str(target.relative_to(ROOT)),
                **info,
            }
        )
    result = {
        "generated_at": now_iso(),
        "snapshot_id": snapshot_id,
        "source_page": SOURCE_PAGE,
        "source_regime": REGIME,
        "files": files,
    }
    write_json(STATE / "latest_snapshot.json", result)
    return result


def read_csv_robust(path: Path) -> tuple[pd.DataFrame, str]:
    last_error: Exception | None = None
    for encoding in ("utf-8-sig", "cp1252", "latin1"):
        try:
            frame = pd.read_csv(
                path,
                dtype=str,
                keep_default_na=False,
                na_filter=False,
                encoding=encoding,
            )
            return frame, encoding
        except UnicodeDecodeError as exc:
            last_error = exc
    assert last_error is not None
    raise last_error


def source_csv_paths(snapshot: dict[str, Any]) -> dict[str, Path]:
    return {x["key"]: ROOT / x["path"] for x in snapshot["files"] if x["key"] in CURRENT_KEYS}


def stage_parse() -> dict[str, Any]:
    snapshot_path = STATE / "latest_snapshot.json"
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8")) if snapshot_path.exists() else stage_snapshot()
    catalog = load_catalog()
    by_key = source_by_key(catalog)
    frames = []
    schemas: dict[str, list[str]] = {}
    encodings: dict[str, str] = {}
    row_counts: dict[str, int] = {}
    for key, path in source_csv_paths(snapshot).items():
        frame, encoding = read_csv_robust(path)
        schemas[key] = list(frame.columns)
        encodings[key] = encoding
        row_counts[key] = int(len(frame))
        frame["__source_key"] = key
        frame["__source_bucket"] = by_key[key]["bucket"]
        frame["__source_file"] = path.name
        frame["__source_url"] = by_key[key]["url"]
        frames.append(frame)
    baseline = schemas[CURRENT_KEYS[0]]
    for key in CURRENT_KEYS[1:]:
        if schemas[key] != baseline:
            raise RuntimeError(f"current NHTSA source schemas diverged: {CURRENT_KEYS[0]} vs {key}")
    all_versions = pd.concat(frames, ignore_index=True)
    all_versions["__report_version_num"] = pd.to_numeric(all_versions["Report Version"], errors="raise").astype(int)
    dupes = all_versions.duplicated(["Report ID", "Report Version"], keep=False)
    if dupes.any():
        raise RuntimeError(f"duplicate Report ID/Report Version pairs found: {int(dupes.sum())} rows")
    DERIVED.mkdir(parents=True, exist_ok=True)
    parsed_path = DERIVED / "current_all_versions.csv"
    all_versions.to_csv(parsed_path, index=False, encoding="utf-8", lineterminator="\n")
    result = {
        "generated_at": now_iso(),
        "snapshot_id": snapshot["snapshot_id"],
        "rows": int(len(all_versions)),
        "unique_report_ids": int(all_versions["Report ID"].nunique()),
        "source_columns": len(baseline),
        "row_counts": row_counts,
        "encodings": encodings,
        "parsed_path": str(parsed_path.relative_to(ROOT)),
        "parsed_sha256": sha256(parsed_path),
        "duplicate_report_id_version_rows": 0,
    }
    write_json(STATE / "parse_report.json", result)
    return result


def stage_rights() -> dict[str, Any]:
    parse_path = STATE / "parse_report.json"
    parse = json.loads(parse_path.read_text(encoding="utf-8")) if parse_path.exists() else stage_parse()
    frame = pd.read_csv(ROOT / parse["parsed_path"], dtype=str, keep_default_na=False, na_filter=False, encoding="utf-8")
    source_hosts_ok = frame["__source_url"].str.startswith("https://static.nhtsa.gov/").all()
    if not source_hosts_ok:
        raise RuntimeError("rights gate failed: non-NHTSA source URL entered parsed data")
    vin = frame["VIN"].astype(str).str.strip()
    vin_lengths = vin[~vin.str.lower().isin({"", "unknown", "unk"})].str.len()
    # NHTSA states only the first 11 VIN characters are public. Do not reject
    # source placeholders, but flag any apparent overlength value.
    overlength_vin_rows = int((vin_lengths > 11).sum())
    if overlength_vin_rows:
        raise RuntimeError(f"rights gate failed: {overlength_vin_rows} apparent VIN values exceed 11 characters")
    result = {
        "generated_at": now_iso(),
        "pass": True,
        "basis": (
            "Only the official NHTSA SGO public CSVs are used. NHTSA states the public release excludes/marks PII and CBI; "
            "the pipeline preserves those redactions and does not enrich from private/unredacted sources."
        ),
        "kaggle_license": "other",
        "source_hosts_ok": bool(source_hosts_ok),
        "apparent_vin_values_over_11_chars": overlength_vin_rows,
        "source_page": SOURCE_PAGE,
    }
    write_json(STATE / "rights_gate.json", result)
    return result


def snake(name: str) -> str:
    value = name.lower().replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", "_", value).strip("_")
    return value


def parse_month(value: str) -> str:
    value = str(value).strip()
    if not value:
        return ""
    dt = pd.to_datetime(value, format="%b-%Y", errors="coerce")
    if pd.isna(dt):
        return ""
    return dt.strftime("%Y-%m")


def field_description(source_name: str | None, normalized_name: str) -> str:
    core = {
        "report_id": "NHTSA-generated identifier that stays with an incident report across later report versions.",
        "report_version": "Sequential NHTSA report version; the release keeps the highest available version for each Report ID.",
        "reporting_entity": "Entity that filed the incident report under the NHTSA Standing General Order.",
        "report_type": "Incident report type selected by the reporting entity under the third-amended SGO (for example 5-Day, Monthly, or Update).",
        "report_submission_date": "Month and year when the incident report was first submitted; this is not a revision timestamp.",
        "same_vehicle_id": "NHTSA-generated linkage identifier intended to show when multiple reported incidents involve the same subject vehicle.",
        "same_incident_id": "NHTSA-generated linkage identifier intended to show when multiple reports refer to the same incident; it is preserved but not used to merge rows.",
        "automation_system_engaged": "Reporting entity's classification of the automation system engaged at the time of the crash: ADS, ADAS, or Unknown/see narrative.",
        "engagement_status": "Reported highest-level automation-system engagement status during the period from 30 seconds before crash onset through crash conclusion.",
        "incident_date": "Incident month and year as published by NHTSA; day-level dates are not public in this release.",
        "narrative": "Public incident narrative as released by NHTSA; PII/CBI redactions are preserved exactly as published.",
        "highest_injury_severity_alleged": "Highest injury severity alleged/reported for the incident in the NHTSA SGO form.",
        "crash_with": "Reported object or road user with which the crash occurred.",
        "vin": "Public VIN portion as released by NHTSA; the last six VIN characters are withheld for privacy.",
    }
    if normalized_name in core:
        return core[normalized_name]
    if source_name is None:
        derived = {
            "source_bucket": "Which current NHTSA source file contained the selected latest report: ADS, Level 2 ADAS, or Other / Unknown.",
            "source_regime": "Reporting regime for this release row: third-amended SGO effective June 16, 2025.",
            "source_file": "Official NHTSA CSV filename from which the selected latest report version was read.",
            "source_url": "Official NHTSA download URL for the source CSV containing the selected latest report version.",
            "incident_month": "Convenience ISO YYYY-MM value derived from the published Incident Date; blank when the source date is unknown/unparseable.",
            "report_submission_month": "Convenience ISO YYYY-MM value derived from Report Submission Date.",
            "versions_observed_in_current_snapshot": "Number of report-version rows for this Report ID present in the current third-amended source snapshot; earlier versions can exist only in the archive.",
        }
        return derived[normalized_name]
    lower = source_name.lower()
    if lower.startswith("weather -"):
        return f"Indicator/value for the NHTSA SGO weather field '{source_name}' in the selected latest report version."
    if lower.startswith("roadway-"):
        return f"Indicator/value for the NHTSA SGO roadway-condition field '{source_name}' in the selected latest report version."
    if lower.startswith("source -"):
        return f"Indicator/value for the reported notice-source field '{source_name}' in the selected latest report version."
    if "contact area" in lower:
        return f"Indicator/value for reported vehicle contact area '{source_name}' in the selected latest report version."
    if lower.startswith("data availability -"):
        return f"Indicator/value showing whether '{source_name}' data was reported available for the incident."
    if "unknown" in lower or lower.endswith("unk"):
        return f"NHTSA SGO unknown/unavailable indicator for '{source_name}' in the selected latest report version."
    if "cbi" in lower:
        return f"Indicator associated with a confidential-business-information claim for '{source_name}' as published by NHTSA."
    return (
        f"Source-faithful NHTSA SGO field '{source_name}' from the selected latest report version; "
        "see the official current Data Element Definitions & Log for full semantics."
    )


def stage_normalize() -> dict[str, Any]:
    rights_path = STATE / "rights_gate.json"
    rights = json.loads(rights_path.read_text(encoding="utf-8")) if rights_path.exists() else stage_rights()
    if not rights.get("pass"):
        raise RuntimeError("rights gate is not passing")
    parse = json.loads((STATE / "parse_report.json").read_text(encoding="utf-8"))
    source = pd.read_csv(ROOT / parse["parsed_path"], dtype=str, keep_default_na=False, na_filter=False, encoding="utf-8")
    source["__report_version_num"] = pd.to_numeric(source["__report_version_num"], errors="raise").astype(int)
    counts = source.groupby("Report ID").size().to_dict()
    latest_idx = source.groupby("Report ID")["__report_version_num"].idxmax()
    latest = source.loc[latest_idx].copy().sort_values(["Report ID"], kind="stable").reset_index(drop=True)

    source_cols = [c for c in latest.columns if not c.startswith("__")]
    mapping = {c: snake(c) for c in source_cols}
    if len(set(mapping.values())) != len(mapping):
        raise RuntimeError("normalized column-name collision; update mapping deliberately")
    latest = latest.rename(columns=mapping)
    latest["source_bucket"] = source.loc[latest_idx, "__source_bucket"].to_numpy()
    latest["source_regime"] = REGIME
    latest["source_file"] = source.loc[latest_idx, "__source_file"].to_numpy()
    latest["source_url"] = source.loc[latest_idx, "__source_url"].to_numpy()
    latest["incident_month"] = latest["incident_date"].map(parse_month)
    latest["report_submission_month"] = latest["report_submission_date"].map(parse_month)
    latest["versions_observed_in_current_snapshot"] = latest["report_id"].map(counts).astype(int)

    # Keep the original source field order, then transparent provenance/derived columns.
    derived_cols = [
        "source_bucket",
        "source_regime",
        "source_file",
        "source_url",
        "incident_month",
        "report_submission_month",
        "versions_observed_in_current_snapshot",
    ]
    latest = latest[[*mapping.values(), *derived_cols]]

    DERIVED.mkdir(parents=True, exist_ok=True)
    RELEASE.mkdir(parents=True, exist_ok=True)
    canonical_path = DERIVED / "canonical_latest.csv"
    release_path = RELEASE / "data.csv"
    latest.to_csv(canonical_path, index=False, encoding="utf-8", lineterminator="\n", quoting=csv.QUOTE_MINIMAL)
    shutil.copyfile(canonical_path, release_path)

    mapping_rows = []
    for src_name, norm_name in mapping.items():
        mapping_rows.append(
            {
                "source_name": src_name,
                "release_name": norm_name,
                "description": field_description(src_name, norm_name),
                "derived": False,
            }
        )
    for name in derived_cols:
        mapping_rows.append(
            {
                "source_name": None,
                "release_name": name,
                "description": field_description(None, name),
                "derived": True,
            }
        )
    write_json(QA / "column_mapping.json", mapping_rows)
    result = {
        "generated_at": now_iso(),
        "rows": int(len(latest)),
        "columns": int(len(latest.columns)),
        "canonical_path": str(canonical_path.relative_to(ROOT)),
        "release_path": str(release_path.relative_to(ROOT)),
        "release_bytes": release_path.stat().st_size,
        "release_sha256": sha256(release_path),
    }
    write_json(STATE / "normalize_report.json", result)
    return result


def stage_qa() -> dict[str, Any]:
    normalize_path = STATE / "normalize_report.json"
    normalize = json.loads(normalize_path.read_text(encoding="utf-8")) if normalize_path.exists() else stage_normalize()
    parse = json.loads((STATE / "parse_report.json").read_text(encoding="utf-8"))
    source = pd.read_csv(ROOT / parse["parsed_path"], dtype=str, keep_default_na=False, na_filter=False, encoding="utf-8")
    out = pd.read_csv(ROOT / normalize["release_path"], dtype=str, keep_default_na=False, na_filter=False, encoding="utf-8")
    source["__v"] = pd.to_numeric(source["__report_version_num"], errors="raise").astype(int)
    out_v = pd.to_numeric(out["report_version"], errors="raise").astype(int)
    max_by_id = source.groupby("Report ID")["__v"].max()
    selected = pd.Series(out_v.to_numpy(), index=out["report_id"])
    latest_mismatch = int((selected.sort_index() != max_by_id.sort_index()).sum())
    if latest_mismatch:
        raise RuntimeError(f"QA failed: {latest_mismatch} rows are not the max Report Version")
    if out["report_id"].duplicated().any():
        raise RuntimeError("QA failed: duplicate report_id in canonical output")
    if len(out) != source["Report ID"].nunique():
        raise RuntimeError("QA failed: source unique Report IDs do not reconcile to output rows")

    incident = pd.to_datetime(out["incident_month"], format="%Y-%m", errors="coerce")
    submission = pd.to_datetime(out["report_submission_month"], format="%Y-%m", errors="coerce")
    same = out["same_incident_id"].astype(str).str.strip()
    same_nonblank = same[same.ne("")]
    same_counts = same_nonblank.value_counts()
    narratives = out["narrative"].astype(str).str.strip()

    bucket_counts_source = {str(k): int(v) for k, v in source["__source_bucket"].value_counts().items()}
    bucket_counts_output = {str(k): int(v) for k, v in out["source_bucket"].value_counts().items()}

    missingness = {}
    for col in out.columns:
        blank = out[col].astype(str).str.strip().eq("")
        missingness[col] = {
            "blank": int(blank.sum()),
            "blank_pct": round(float(blank.mean() * 100), 3),
        }

    source_same_change = 0
    for _, group in source.groupby("Report ID"):
        values = group["Same Incident ID"].astype(str).str.strip().replace("", pd.NA).dropna()
        if values.nunique() > 1:
            source_same_change += 1

    qa = {
        "pass": True,
        "source_rows": int(len(source)),
        "source_unique_report_ids": int(source["Report ID"].nunique()),
        "output_rows": int(len(out)),
        "output_columns": int(len(out.columns)),
        "source_bucket_rows": bucket_counts_source,
        "output_bucket_rows": bucket_counts_output,
        "duplicate_report_id_version_rows": int(source.duplicated(["Report ID", "Report Version"], keep=False).sum()),
        "duplicate_output_report_ids": int(out["report_id"].duplicated(keep=False).sum()),
        "latest_version_mismatches": latest_mismatch,
        "max_report_version": int(out_v.max()),
        "report_ids_with_multiple_versions_in_current_snapshot": int((source.groupby("Report ID").size() > 1).sum()),
        "report_ids_with_same_incident_id_change_across_versions": source_same_change,
        "same_incident_ids_linking_multiple_output_report_ids": int((same_counts > 1).sum()),
        "output_rows_in_multi_report_same_incident_ids": int(same_counts[same_counts > 1].sum()),
        "incident_month_min": None if incident.dropna().empty else incident.min().strftime("%Y-%m"),
        "incident_month_max": None if incident.dropna().empty else incident.max().strftime("%Y-%m"),
        "incident_month_blank_or_unparseable": int(incident.isna().sum()),
        "report_submission_month_min": None if submission.dropna().empty else submission.min().strftime("%Y-%m"),
        "report_submission_month_max": None if submission.dropna().empty else submission.max().strftime("%Y-%m"),
        "narrative_nonblank_rows": int(narratives.ne("").sum()),
        "narrative_nonblank_pct": round(float(narratives.ne("").mean() * 100), 3),
        "redaction_marker_rows": int(
            out.astype(str).apply(lambda s: s.str.contains(r"REDACTED|PERSONALLY IDENTIFIABLE|\[XXX\]", case=False, regex=True)).any(axis=1).sum()
        ),
        "missingness": missingness,
        "anomalies_preserved": [
            "Rows in the Other / Unknown bucket are retained rather than forced into ADS or Level 2 ADAS.",
            "Multiple Report IDs sharing a Same Incident ID are retained as separate rows.",
            "Same Incident ID can change across report versions; the selected latest report value is preserved.",
            "Incident month can predate the June 16, 2025 regime boundary because later report updates can describe older incidents.",
        ],
        "release_bytes": (ROOT / normalize["release_path"]).stat().st_size,
        "release_sha256": sha256(ROOT / normalize["release_path"]),
    }
    write_json(QA / "qa_report.json", qa)
    return qa


def git_sha() -> str | None:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return None


def stage_manifest() -> dict[str, Any]:
    qa_path = QA / "qa_report.json"
    qa = json.loads(qa_path.read_text(encoding="utf-8")) if qa_path.exists() else stage_qa()
    snapshot = json.loads((STATE / "latest_snapshot.json").read_text(encoding="utf-8"))
    normalize = json.loads((STATE / "normalize_report.json").read_text(encoding="utf-8"))
    manifest = {
        "generated_at": now_iso(),
        "git_sha": git_sha(),
        "source_page": SOURCE_PAGE,
        "source_regime": REGIME,
        "snapshot_id": snapshot["snapshot_id"],
        "source_files": snapshot["files"],
        "release": {
            "path": normalize["release_path"],
            "rows": qa["output_rows"],
            "columns": qa["output_columns"],
            "bytes": qa["release_bytes"],
            "sha256": qa["release_sha256"],
            "grain": "one row per NHTSA Report ID, latest available Report Version in the current third-amended files",
        },
        "rights_gate": json.loads((STATE / "rights_gate.json").read_text(encoding="utf-8")),
        "qa_pass": qa["pass"],
    }
    write_json(QA / "release_manifest.json", manifest)
    return manifest


def run_all() -> None:
    steps = [
        ("discover", stage_discover),
        ("snapshot", stage_snapshot),
        ("parse", stage_parse),
        ("rights", stage_rights),
        ("normalize", stage_normalize),
        ("qa", stage_qa),
        ("manifest", stage_manifest),
    ]
    for i, (name, func) in enumerate(steps, 1):
        print(f"[{i}/{len(steps)}] {name}")
        result = func()
        print(json.dumps({k: v for k, v in result.items() if k in {"pass", "rows", "columns", "snapshot_id", "output_rows", "release_sha256"}}, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(description="Restartable NHTSA SGO dataset pipeline")
    parser.add_argument(
        "stage",
        choices=("discover", "snapshot", "parse", "rights", "normalize", "qa", "manifest", "all"),
        default="all",
        nargs="?",
    )
    args = parser.parse_args()
    if args.stage == "all":
        run_all()
        return
    funcs = {
        "discover": stage_discover,
        "snapshot": stage_snapshot,
        "parse": stage_parse,
        "rights": stage_rights,
        "normalize": stage_normalize,
        "qa": stage_qa,
        "manifest": stage_manifest,
    }
    print(json.dumps(funcs[args.stage](), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
