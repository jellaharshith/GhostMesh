"""UCDP (Uppsala Conflict Data Program) adapter → normalized Event list.

Live API: https://ucdpapi.pcr.uu.se/api/
No auth required. Falls back to data/seed/ucdp_sample.json.

UCDP data covers:
- Armed Conflict Dataset (ACD) — conflict-year level
- Georeferenced Event Dataset (GED) — incident level
- Battle-Related Deaths Dataset

Schema maps to the same Event model as acled_adapter / gdelt_adapter.
"""
from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import List, Optional

import requests

from .schemas import Event, make_event_id
from .infra import tag as infra_tag

logger = logging.getLogger(__name__)

_UCDP_GED_URL = "https://ucdpapi.pcr.uu.se/api/gedevents/24.1"
_SEED = Path(__file__).parents[1] / "data" / "seed" / "ucdp_sample.json"

_INTENSITY_MAP = {
    1: "diplomatic",   # minor conflict (<25 battle deaths/year)
    2: "armed-conflict",  # war (≥1000 battle deaths/year)
}


def _ucdp_row_to_event(row: dict) -> Event:
    conflict_name = row.get("conflict_name", row.get("dyad_name", "Unknown conflict"))
    country = row.get("country", "")
    region = row.get("region", "")
    location = f"{country}" if country else region
    year = str(row.get("year", ""))
    start_date = row.get("start_date", year)

    intensity = int(row.get("intensity_level", 1))
    event_type = _INTENSITY_MAP.get(intensity, "other")

    notes = row.get("notes", "")[:280]
    cid = row.get("conflict_id", conflict_name + country)

    # Infer actors from dyad name
    dyad = row.get("dyad_name", "")
    actors = [a.strip() for a in dyad.split(" - ")] if " - " in dyad else [conflict_name]

    # Tension weight: war = 0.9, minor = 0.5
    tension_weight = 0.9 if intensity == 2 else 0.5

    return Event(
        event_id=make_event_id("ucdp", cid),
        source="ucdp",
        timestamp=start_date,
        location=location,
        actors=actors,
        event_type=event_type,
        summary=notes or f"{conflict_name} — {location}",
        tension_weight=tension_weight,
        infrastructure_relevance=infra_tag(notes),
    )


def _load_seed() -> List[dict]:
    try:
        return json.loads(_SEED.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.debug("UCDP seed load failed: %s", exc)
        return []


def _fetch_live(
    country: Optional[str] = None,
    year: int = 2024,
    limit: int = 20,
    timeout_s: float = 6.0,
) -> List[dict]:
    """Fetch from UCDP GED API. No auth required."""
    params: dict = {
        "Year": year,
        "pagesize": limit,
        "page": 1,
    }
    if country:
        params["Country"] = country
    resp = requests.get(_UCDP_GED_URL, params=params, timeout=timeout_s)
    resp.raise_for_status()
    data = resp.json()
    # GED returns {"Result": [...], "TotalCount": N}
    return data.get("Result", []) or []


def fetch(
    query: str = "",
    country: Optional[str] = None,
    timeout_s: float = 5.0,
) -> List[Event]:
    """
    Fetch UCDP conflict events. Falls back to seed data if API unavailable.
    Never raises.
    """
    raw: List[dict] = []

    # Try live API
    try:
        raw = _fetch_live(country=country, timeout_s=timeout_s)
        if raw:
            logger.info("UCDP: fetched %d events live", len(raw))
    except Exception as exc:
        logger.debug("UCDP live fetch failed: %s", exc)

    # Fall back to seed
    if not raw:
        logger.debug("UCDP: using seed fallback")
        raw = _load_seed()
        # Filter by query keyword if provided
        if query:
            ql = query.lower()
            raw = [r for r in raw if ql in json.dumps(r).lower()] or raw

    events: List[Event] = []
    for row in raw:
        try:
            events.append(_ucdp_row_to_event(row))
        except Exception as exc:
            logger.debug("UCDP row parse error: %s", exc)
    return events
