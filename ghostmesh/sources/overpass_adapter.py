"""Overpass / OpenStreetMap infrastructure adapter.

Attempts a live Overpass query (no auth required).
Falls back to data/seed/osm_sample.json on any failure.
Never raises.

Region → bbox mapping: call bbox_for_region(region_text) to get a
"south,west,north,east" string for common geopolitical regions and countries.
"""
from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

# ── Region → bounding box map ─────────────────────────────────────────────────
# Format: "south,west,north,east" (decimal degrees)
# Covers named regions, countries, and common scenario theaters
_REGION_BBOX: Dict[str, str] = {
    # US regions
    "united states":          "24.5,-125.0,49.5,-66.9",
    "us":                     "24.5,-125.0,49.5,-66.9",
    "usa":                    "24.5,-125.0,49.5,-66.9",
    "northeast us":           "38.9,-80.0,47.5,-66.9",
    "mid-atlantic":           "36.5,-80.5,42.5,-73.5",
    "east coast":             "24.5,-82.0,47.5,-66.9",
    "texas":                  "25.8,-107.0,36.5,-93.5",
    "gulf coast":             "25.0,-97.5,31.0,-80.0",
    "dc":                     "38.7,-77.3,39.1,-76.8",
    "washington dc":          "38.7,-77.3,39.1,-76.8",

    # Europe
    "europe":                 "34.5,-10.0,71.5,40.0",
    "eastern europe":         "44.0,14.0,71.5,40.0",
    "ukraine":                "44.0,22.1,52.4,40.2",
    "poland":                 "49.0,14.1,54.9,24.2",
    "baltic":                 "53.9,20.9,59.7,28.3",
    "germany":                "47.2,5.9,55.1,15.0",
    "nato eastern flank":     "44.0,14.0,60.0,30.0",

    # Asia-Pacific
    "taiwan":                 "21.9,119.9,26.4,122.1",
    "taiwan strait":          "20.0,117.0,28.0,124.0",
    "south china sea":        "0.0,100.0,25.0,125.0",
    "korea":                  "33.1,124.5,38.6,131.0",
    "south korea":            "33.1,124.5,38.6,131.0",
    "japan":                  "24.2,122.7,45.6,145.8",
    "indo-pacific":           "-10.0,95.0,40.0,180.0",

    # Middle East
    "middle east":            "12.0,25.0,42.0,63.0",
    "iran":                   "25.0,44.0,40.0,63.5",
    "gulf":                   "22.0,48.0,29.0,58.0",
    "persian gulf":           "22.0,48.0,29.0,58.0",
    "israel":                 "29.5,34.2,33.4,35.9",

    # Africa
    "africa":                 "-35.0,-20.0,38.0,55.0",
    "sahel":                  "10.0,-18.0,25.0,25.0",

    # Global fallback
    "global":                 None,
}


def bbox_for_region(region_text: str) -> Optional[str]:
    """
    Map a free-text region description to an Overpass bbox string.
    Returns None if no match found (triggers seed fallback).

    Example:
        bbox_for_region("Taiwan Strait crisis")  → "20.0,117.0,28.0,124.0"
        bbox_for_region("Volt Typhoon Texas")    → "25.8,-107.0,36.5,-93.5"
    """
    if not region_text:
        return None
    text = region_text.lower()
    # Exact match first
    if text in _REGION_BBOX:
        return _REGION_BBOX[text]
    # Substring scan (longest key that appears in the text wins)
    best_key = None
    best_len = 0
    for key, bbox in _REGION_BBOX.items():
        if key in text and len(key) > best_len:
            best_key = key
            best_len = len(key)
    if best_key:
        return _REGION_BBOX[best_key]
    return None

_OVERPASS_URL = "https://overpass-api.de/api/interpreter"
_SEED = Path(__file__).parents[1] / "data" / "seed" / "osm_sample.json"

_INFRA_TAGS = [
    "power=substation", "power=plant",
    "man_made=water_works", "pipeline=fuel",
    "telecom=exchange", "port=terminal",
]

# Criticality heuristics from OSM tags
_CRITICALITY_MAP = {
    "nuclear": "critical",
    "exchange": "critical",
    "pipeline": "critical",
    "substation": "high",
    "water_works": "high",
    "terminal": "high",
    "plant": "medium",
}


def _infer_criticality(tags: Dict[str, str]) -> str:
    combined = " ".join(tags.values()).lower()
    for kw, level in _CRITICALITY_MAP.items():
        if kw in combined:
            return level
    return "medium"


def _overpass_element_to_record(el: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    tags = el.get("tags", {})
    if not tags:
        return None
    name = tags.get("name") or tags.get("operator") or "Unknown facility"
    lat = el.get("lat") or (el.get("center", {}) or {}).get("lat")
    lon = el.get("lon") or (el.get("center", {}) or {}).get("lon")
    infra_type = (
        tags.get("power") or
        tags.get("man_made") or
        tags.get("pipeline") or
        tags.get("telecom") or
        tags.get("port") or
        "facility"
    )
    criticality = _infer_criticality(tags)
    return {
        "id": f"{el.get('type','')}/{el.get('id','')}",
        "type": infra_type,
        "name": name,
        "location": tags.get("addr:city") or tags.get("addr:state") or "",
        "lat": lat,
        "lon": lon,
        "tags": tags,
        "criticality": criticality,
        "risk_label": f"{infra_type.title()} infrastructure — {criticality} criticality",
    }


def _fetch_live(bbox: str, timeout_s: float = 6.0) -> List[Dict[str, Any]]:
    """
    bbox: "south,west,north,east" e.g. "38.5,-77.5,40.2,-74.5"
    Returns list of infrastructure records.
    """
    tag_union = "\n".join(
        f'  node["{t.split("=")[0]}"="{t.split("=")[1]}"]({bbox});'
        f'  way["{t.split("=")[0]}"="{t.split("=")[1]}"]({bbox});'
        for t in _INFRA_TAGS
    )
    query = f"""
[out:json][timeout:25];
(
{tag_union}
);
out center 20;
"""
    resp = requests.post(_OVERPASS_URL, data={"data": query}, timeout=timeout_s)
    resp.raise_for_status()
    elements = resp.json().get("elements", [])
    records = []
    for el in elements:
        rec = _overpass_element_to_record(el)
        if rec:
            records.append(rec)
    return records


def _load_seed() -> List[Dict[str, Any]]:
    try:
        return json.loads(_SEED.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.debug("OSM seed load failed: %s", exc)
        return []


def fetch(
    bbox: Optional[str] = None,
    timeout_s: float = 6.0,
) -> List[Dict[str, Any]]:
    """
    Fetch critical infrastructure near bbox.
    Falls back to committed seed data if Overpass is unavailable.
    """
    if bbox:
        try:
            records = _fetch_live(bbox, timeout_s=timeout_s)
            if records:
                logger.info("Overpass: fetched %d infrastructure nodes", len(records))
                return records
        except Exception as exc:
            logger.debug("Overpass live fetch failed: %s", exc)

    logger.debug("Overpass: using seed fallback")
    return _load_seed()


def filter_by_criticality(
    records: List[Dict[str, Any]],
    min_level: str = "high",
) -> List[Dict[str, Any]]:
    """Return records at or above min_level criticality."""
    order = {"critical": 3, "high": 2, "medium": 1, "low": 0}
    threshold = order.get(min_level, 1)
    return [r for r in records if order.get(r.get("criticality", "low"), 0) >= threshold]
