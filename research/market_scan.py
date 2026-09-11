from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from kaggle.api.kaggle_api_extended import KaggleApi


SEARCHES = [
    "automated driving crash reports",
    "autonomous driving crashes",
    "self driving car accidents",
    "ADAS crashes",
    "NHTSA",
    "traffic accidents US",
    "vehicle crashes US",
    "traffic fatalities NHTSA",
    "road accidents",
]


def main() -> None:
    api = KaggleApi()
    api.authenticate()
    by_ref: dict[str, dict] = {}
    now = datetime.now(timezone.utc)

    for query in SEARCHES:
        for page in (1, 2):
            for dataset in api.dataset_list(search=query, page=page) or []:
                if dataset is None:
                    continue
                item = dataset.to_dict()
                ref = item.get("ref")
                if not ref:
                    continue
                updated = item.get("lastUpdated")
                update_age_days = None
                if updated:
                    dt = datetime.fromisoformat(updated.replace("Z", "+00:00"))
                    update_age_days = (now - dt).days
                existing = by_ref.setdefault(
                    ref,
                    {
                        "ref": ref,
                        "title": item.get("title"),
                        "subtitle": item.get("subtitle"),
                        "url": item.get("url"),
                        "last_updated": updated,
                        "update_age_days": update_age_days,
                        "size_bytes": item.get("totalBytes"),
                        "downloads": item.get("downloadCount"),
                        "votes": item.get("voteCount"),
                        "views": item.get("viewCount"),
                        "notebooks": item.get("kernelCount"),
                        "license": item.get("licenseName"),
                        "version": item.get("currentVersionNumber"),
                        "usability": item.get("usabilityRating"),
                        "queries": [],
                    },
                )
                existing["queries"].append(query)

    values = list(by_ref.values())
    values.sort(
        key=lambda x: (
            x.get("votes") or 0,
            x.get("downloads") or 0,
            x.get("views") or 0,
        ),
        reverse=True,
    )
    out = {
        "generated_at": now.isoformat(),
        "searches": SEARCHES,
        "candidate_count": len(values),
        "candidates": values,
    }
    path = Path("research/market_candidates.json")
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {path} with {len(values)} unique candidates")
    for item in values[:40]:
        downloads = item.get("downloads")
        views = item.get("views")
        notebooks = item.get("notebooks")
        print(
            f"{item['ref']:<70} votes={item['votes']:<5} "
            f"downloads={str(downloads):<8} views={str(views):<9} "
            f"notebooks={str(notebooks):<5} bytes={item['size_bytes']}"
        )


if __name__ == "__main__":
    main()
