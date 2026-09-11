from __future__ import annotations

import hashlib
import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "state" / "source_catalog.json"
RAW = ROOT / "data" / "raw" / "pilot"
QA = ROOT / "qa"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, path: Path) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size > 0:
        return {"downloaded": False, "bytes": path.stat().st_size, "sha256": sha256(path)}
    tmp = path.with_suffix(path.suffix + ".part")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 NHTSA-Kaggle-Pilot/1.0"})
    start = time.perf_counter()
    with urllib.request.urlopen(req, timeout=120) as response, tmp.open("wb") as out:
        while True:
            block = response.read(1024 * 1024)
            if not block:
                break
            out.write(block)
    tmp.replace(path)
    return {
        "downloaded": True,
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "seconds": round(time.perf_counter() - start, 3),
    }


def read_csv_lossless(path: Path) -> pd.DataFrame:
    # NHTSA files are CSVs with narrative text. The Python parser is more tolerant
    # of embedded punctuation/quotes than shell tooling and preserves strings.
    last_error: Exception | None = None
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return pd.read_csv(
                path,
                dtype=str,
                keep_default_na=False,
                na_filter=False,
                encoding=encoding,
            )
        except UnicodeDecodeError as exc:
            last_error = exc
    assert last_error is not None
    raise last_error


def norm(s: str) -> str:
    return " ".join(str(s).strip().lower().replace("_", " ").split())


def find_col(columns: list[str], *needles: str) -> str | None:
    index = {norm(c): c for c in columns}
    for needle in needles:
        n = norm(needle)
        if n in index:
            return index[n]
    for c in columns:
        cn = norm(c)
        if all(token in cn for token in norm(needles[0]).split()):
            return c
    return None


def date_values(df: pd.DataFrame) -> dict[str, Any]:
    cols = list(df.columns)
    date_col = find_col(cols, "Incident Date")
    if date_col:
        parsed = pd.to_datetime(df[date_col], format="%b-%Y", errors="coerce")
        valid = parsed.dropna()
        return {
            "date_col": date_col,
            "min": None if valid.empty else valid.min().strftime("%Y-%m"),
            "max": None if valid.empty else valid.max().strftime("%Y-%m"),
            "valid_values": int(parsed.notna().sum()),
            "invalid_or_blank": int(parsed.isna().sum()),
        }
    month_col = find_col(cols, "Incident Month")
    year_col = find_col(cols, "Incident Year")
    if not month_col or not year_col:
        return {"month_col": month_col, "year_col": year_col, "min": None, "max": None}
    vals: list[str] = []
    for m, y in zip(df[month_col], df[year_col]):
        m = str(m).strip()
        y = str(y).strip()
        if y.isdigit() and len(y) == 4 and m.isdigit() and 1 <= int(m) <= 12:
            vals.append(f"{int(y):04d}-{int(m):02d}")
    return {
        "month_col": month_col,
        "year_col": year_col,
        "min": min(vals) if vals else None,
        "max": max(vals) if vals else None,
        "valid_values": len(vals),
    }


def profile_csv(source: dict[str, Any], path: Path) -> dict[str, Any]:
    started = time.perf_counter()
    df = read_csv_lossless(path)
    cols = list(df.columns)
    report_id = find_col(cols, "Report ID")
    report_version = find_col(cols, "Report Version")
    same_incident = find_col(cols, "Same Incident ID")
    same_vehicle = find_col(cols, "Same Vehicle ID")
    narrative = find_col(cols, "Narrative")
    missing = {}
    for col in cols:
        blank = df[col].astype(str).str.strip().eq("")
        unknown = df[col].astype(str).str.strip().str.lower().isin({"unknown", "unk", "unknown, see narrative"})
        redacted = df[col].astype(str).str.contains(r"REDACTED|PERSONALLY IDENTIFIABLE|\[XXX\]", case=False, regex=True)
        missing[col] = {
            "blank": int(blank.sum()),
            "blank_pct": round(float(blank.mean() * 100), 3),
            "unknown": int(unknown.sum()),
            "redacted": int(redacted.sum()),
        }
    report_versions: dict[str, Any] = {}
    if report_id and report_version:
        vnum = pd.to_numeric(df[report_version], errors="coerce")
        counts = df.groupby(report_id, dropna=False).size()
        latest = vnum.groupby(df[report_id]).max()
        report_versions = {
            "unique_report_ids": int(df[report_id].nunique(dropna=False)),
            "rows_with_duplicate_report_id": int(df.duplicated(report_id, keep=False).sum()),
            "report_ids_with_multiple_versions": int((counts > 1).sum()),
            "max_report_version": None if vnum.dropna().empty else int(vnum.max()),
            "report_ids_where_row_count_differs_from_max_version": int(sum(int(counts.get(k, 0)) != int(v) for k, v in latest.dropna().items())),
        }
    narrative_stats = None
    if narrative:
        text = df[narrative].astype(str).str.strip()
        narrative_stats = {
            "available_rows": int(text.ne("").sum()),
            "available_pct": round(float(text.ne("").mean() * 100), 3),
            "median_chars_nonblank": round(float(text[text.ne("")].str.len().median()), 1) if text.ne("").any() else 0,
            "max_chars": int(text.str.len().max()) if len(text) else 0,
        }
    same_incident_stats = None
    if same_incident:
        ids = df[same_incident].astype(str).str.strip()
        nonblank = ids[ids.ne("")]
        counts = nonblank.value_counts()
        same_incident_stats = {
            "nonblank_rows": int(nonblank.size),
            "unique_nonblank": int(nonblank.nunique()),
            "ids_with_multiple_rows": int((counts > 1).sum()),
            "rows_in_multirow_ids": int(counts[counts > 1].sum()),
        }
    return {
        "key": source["key"],
        "regime": source["regime"],
        "bucket": source.get("bucket"),
        "url": source["url"],
        "path": str(path.relative_to(ROOT)),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "rows": int(len(df)),
        "columns": len(cols),
        "column_names": cols,
        "date_range": date_values(df),
        "report_id_col": report_id,
        "report_version_col": report_version,
        "same_incident_id_col": same_incident,
        "same_vehicle_id_col": same_vehicle,
        "exact_duplicate_rows": int(df.duplicated(keep=False).sum()),
        "report_versions": report_versions,
        "same_incident": same_incident_stats,
        "narrative": narrative_stats,
        "missingness": missing,
        "parse_seconds": round(time.perf_counter() - started, 3),
    }


def main() -> None:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    observed = datetime.fromisoformat(catalog["observed_at"])
    age_days = (datetime.now(timezone.utc) - observed.astimezone(timezone.utc)).total_seconds() / 86400
    if age_days > 45:
        raise SystemExit(f"source catalog is {age_days:.1f} days old; refresh from the live NHTSA page before downloading")

    csv_profiles = []
    files = []
    for src in catalog["sources"]:
        # Pilot downloads all six cumulative CSVs plus both data dictionaries.
        # The order PDF is rights/regime documentation, not needed for schema metrics.
        if src["key"] == "third_amended_order":
            continue
        group = "current" if src["regime"] == "third_amended_sgo" else "archive"
        filename = src["url"].rsplit("/", 1)[-1]
        path = RAW / group / filename
        info = download(src["url"], path)
        files.append({"key": src["key"], "url": src["url"], "path": str(path.relative_to(ROOT)), **info})
        if src["kind"] == "csv":
            csv_profiles.append(profile_csv(src, path))

    schemas = {p["key"]: p["column_names"] for p in csv_profiles}
    current_cols = set().union(*(set(v) for k, v in schemas.items() if k.startswith("current_")))
    archive_cols = set().union(*(set(v) for k, v in schemas.items() if k.startswith("archive_")))
    schema_diff = {
        "current_union_columns": len(current_cols),
        "archive_union_columns": len(archive_cols),
        "only_current": sorted(current_cols - archive_cols),
        "only_archive": sorted(archive_cols - current_cols),
        "common": len(current_cols & archive_cols),
    }

    def combine(regime_prefix: str) -> pd.DataFrame:
        frames = []
        for src in catalog["sources"]:
            if src["kind"] != "csv" or not src["key"].startswith(regime_prefix + "_"):
                continue
            group = "current" if src["regime"] == "third_amended_sgo" else "archive"
            path = RAW / group / src["url"].rsplit("/", 1)[-1]
            frame = read_csv_lossless(path)
            frame["__source_key"] = src["key"]
            frame["__source_bucket"] = src.get("bucket", "")
            frames.append(frame)
        return pd.concat(frames, ignore_index=True)

    combined_stats: dict[str, Any] = {}
    combined_frames: dict[str, pd.DataFrame] = {}
    for prefix in ("current", "archive"):
        frame = combine(prefix)
        combined_frames[prefix] = frame
        version = pd.to_numeric(frame["Report Version"], errors="coerce")
        frame = frame.assign(__version_num=version)
        grouped = frame.groupby("Report ID", dropna=False)["__version_num"].agg(["count", "max"])
        latest_idx = frame.groupby("Report ID", dropna=False)["__version_num"].idxmax()
        latest = frame.loc[latest_idx].copy()
        same_latest = latest["Same Incident ID"].astype(str).str.strip()
        same_latest_nonblank = same_latest[same_latest.ne("")]
        same_latest_counts = same_latest_nonblank.value_counts()
        same_incident_changes = 0
        bucket_changes = 0
        for _, group in frame.groupby("Report ID", dropna=False):
            if group["Same Incident ID"].astype(str).str.strip().replace("", pd.NA).dropna().nunique() > 1:
                same_incident_changes += 1
            if group["__source_bucket"].nunique() > 1:
                bucket_changes += 1
        incident_dates = pd.to_datetime(frame["Incident Date"], format="%b-%Y", errors="coerce")
        submission_dates = pd.to_datetime(frame["Report Submission Date"], format="%b-%Y", errors="coerce")
        combined_stats[prefix] = {
            "rows": int(len(frame)),
            "unique_report_ids": int(frame["Report ID"].nunique(dropna=False)),
            "unique_report_id_version_pairs": int(frame[["Report ID", "Report Version"]].drop_duplicates().shape[0]),
            "duplicate_report_id_version_rows": int(frame.duplicated(["Report ID", "Report Version"], keep=False).sum()),
            "report_ids_with_multiple_versions": int((grouped["count"] > 1).sum()),
            "max_report_version": int(version.max()) if version.notna().any() else None,
            "report_ids_where_observed_version_count_differs_from_max_version": int((grouped["count"] != grouped["max"]).sum()),
            "latest_report_rows": int(len(latest)),
            "latest_bucket_counts": {str(k): int(v) for k, v in latest["__source_bucket"].value_counts().items()},
            "latest_same_incident_ids_with_multiple_report_ids": int((same_latest_counts > 1).sum()),
            "latest_rows_in_multi_report_same_incident_ids": int(same_latest_counts[same_latest_counts > 1].sum()),
            "report_ids_where_same_incident_id_changes_across_versions": same_incident_changes,
            "report_ids_where_source_bucket_changes_across_versions": bucket_changes,
            "incident_date_min": None if incident_dates.dropna().empty else incident_dates.min().strftime("%Y-%m"),
            "incident_date_max": None if incident_dates.dropna().empty else incident_dates.max().strftime("%Y-%m"),
            "incident_date_unparseable_or_blank": int(incident_dates.isna().sum()),
            "submission_date_min": None if submission_dates.dropna().empty else submission_dates.min().strftime("%Y-%m"),
            "submission_date_max": None if submission_dates.dropna().empty else submission_dates.max().strftime("%Y-%m"),
        }

    current_ids = set(combined_frames["current"]["Report ID"])
    archive_ids = set(combined_frames["archive"]["Report ID"])
    cross_regime_ids = current_ids & archive_ids
    cross_regime = {
        "overlapping_report_ids": len(cross_regime_ids),
        "examples": [],
    }
    for rid in sorted(cross_regime_ids)[:20]:
        a = combined_frames["archive"].loc[combined_frames["archive"]["Report ID"] == rid]
        c = combined_frames["current"].loc[combined_frames["current"]["Report ID"] == rid]
        cross_regime["examples"].append(
            {
                "report_id": rid,
                "archive_versions": sorted(a["Report Version"].unique().tolist()),
                "current_versions": sorted(c["Report Version"].unique().tolist()),
                "archive_buckets": sorted(a["__source_bucket"].unique().tolist()),
                "current_buckets": sorted(c["__source_bucket"].unique().tolist()),
            }
        )

    total_csv_bytes = sum(p["bytes"] for p in csv_profiles)
    total_rows = sum(p["rows"] for p in csv_profiles)
    current_rows = sum(p["rows"] for p in csv_profiles if p["key"].startswith("current_"))
    archive_rows = sum(p["rows"] for p in csv_profiles if p["key"].startswith("archive_"))
    # A single canonical CSV generally lands between the raw CSV total and ~1.7x
    # after provenance/regime columns are added. This is intentionally an estimate.
    likely_final = {
        "current_regime_only_bytes_low": int(sum(p["bytes"] for p in csv_profiles if p["key"].startswith("current_")) * 1.0),
        "current_regime_only_bytes_high": int(sum(p["bytes"] for p in csv_profiles if p["key"].startswith("current_")) * 1.7),
        "all_regimes_bytes_low": int(total_csv_bytes * 1.0),
        "all_regimes_bytes_high": int(total_csv_bytes * 1.7),
    }
    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "catalog_observed_at": catalog["observed_at"],
        "files": files,
        "csv_profiles": csv_profiles,
        "schema_diff": schema_diff,
        "combined_stats": combined_stats,
        "cross_regime": cross_regime,
        "totals": {
            "pilot_files": len(files),
            "pilot_bytes": sum(f["bytes"] for f in files),
            "csv_bytes": total_csv_bytes,
            "rows": total_rows,
            "current_rows": current_rows,
            "archive_rows": archive_rows,
        },
        "likely_final_csv_size": likely_final,
        "rebuild_complexity": {
            "source_csv_files": 6,
            "source_pdf_files": 2,
            "network_payload_bytes": sum(f["bytes"] for f in files),
            "assessment": "low network/compute cost; primary complexity is semantic harmonization across reporting regimes",
        },
    }
    QA.mkdir(parents=True, exist_ok=True)
    out = QA / "pilot_report.json"
    out.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(output["totals"], indent=2))
    print(json.dumps(schema_diff, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
