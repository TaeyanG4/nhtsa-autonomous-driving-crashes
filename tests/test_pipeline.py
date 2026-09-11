from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pipeline  # noqa: E402


def test_snake_names_core_fields() -> None:
    assert pipeline.snake("Report ID") == "report_id"
    assert pipeline.snake("Automation System Engaged?") == "automation_system_engaged"
    assert pipeline.snake("Within ODD? - CBI") == "within_odd_cbi"


def test_parse_month() -> None:
    assert pipeline.parse_month("JUL-2026") == "2026-07"
    assert pipeline.parse_month("") == ""
    assert pipeline.parse_month("unknown") == ""


def test_catalog_points_to_official_page() -> None:
    catalog = pipeline.load_catalog()
    assert catalog["source_page"] == pipeline.SOURCE_PAGE
    assert all(item["url"].startswith("https://") for item in catalog["sources"])
