from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from kaggle.api.kaggle_api_extended import KaggleApi


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "state" / "adoption"
TARGET = "taeyangg4/nhtsa-autonomous-driving-crashes"
DIRECT_ALTERNATIVE = "darkmatternet/automated-driving-crash-reports"


def find_dataset(api: KaggleApi, ref: str) -> dict | None:
    owner, slug = ref.split("/", 1)
    queries = [slug.replace("-", " "), slug, owner]
    for query in queries:
        for page in range(1, 4):
            for item in api.dataset_list(search=query, page=page) or []:
                if item is not None and item.ref == ref:
                    return item.to_dict()
    return None


def compact(item: dict | None) -> dict | None:
    if item is None:
        return None
    return {
        "ref": item.get("ref"),
        "title": item.get("title"),
        "last_updated": item.get("lastUpdated"),
        "downloads": item.get("downloadCount"),
        "votes": item.get("voteCount"),
        "views": item.get("viewCount"),
        "notebooks": item.get("kernelCount"),
        "size_bytes": item.get("totalBytes"),
        "version": item.get("currentVersionNumber"),
        "usability": item.get("usabilityRating"),
    }


def diagnose(current: dict | None, previous: dict | None) -> str:
    if current is None:
        return "Dataset is not visible in Kaggle public search yet; verify publication/readiness before interpreting adoption."
    if previous is None:
        return "Launch baseline captured; wait for the next checkpoint before attributing funnel performance."
    cv, cd, cw = current.get("views") or 0, current.get("downloads") or 0, current.get("votes") or 0
    pv, pd, pw = previous.get("views") or 0, previous.get("downloads") or 0, previous.get("votes") or 0
    dv, dd, dw = cv - pv, cd - pd, cw - pw
    if dv <= 5:
        return "Low new views: focus on title/subtitle/cover/tags/discoverability before changing the data."
    if dd <= 0 or dd / max(dv, 1) < 0.08:
        return "Views are arriving but download conversion is weak: clarify the first use case and file/value proposition."
    if dd > 0 and dw <= 0:
        return "Downloads are growing without votes: strengthen differentiation and the showcase notebook rather than adding file variants."
    return "Adoption is progressing across the funnel; prioritize stable updates and external notebook/comment signals."


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", default="checkpoint")
    args = parser.parse_args()

    api = KaggleApi()
    # Public dataset_list works without revealing credential material; authenticate
    # opportunistically so owner/private state can also resolve during launch.
    try:
        api.authenticate()
    except Exception:
        pass

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    previous_files = sorted(OUT_DIR.glob("*.json"))
    previous = None
    if previous_files:
        old = json.loads(previous_files[-1].read_text(encoding="utf-8"))
        previous = old.get("target")

    target = compact(find_dataset(api, TARGET))
    alternative = compact(find_dataset(api, DIRECT_ALTERNATIVE))
    observed = datetime.now(timezone.utc)
    result = {
        "observed_at": observed.isoformat(),
        "label": args.label,
        "target": target,
        "direct_alternative": alternative,
        "diagnosis": diagnose(target, previous),
    }
    filename = f"{observed.strftime('%Y%m%dT%H%M%SZ')}-{args.label}.json"
    path = OUT_DIR / filename
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"saved {path}")


if __name__ == "__main__":
    main()
