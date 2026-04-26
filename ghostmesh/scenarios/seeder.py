"""Scenario seeder: canned scenarios + optional GDELT-seeded scenarios."""
from __future__ import annotations
import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

CANNED_DIR = Path(__file__).parent / "canned"
DEFAULT_SCENARIO_ID = "tidewatch-001"

_active: Optional[Dict[str, Any]] = None
_lock = threading.Lock()


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def list_canned() -> List[Dict[str, Any]]:
    """Load all canned/*.json scenarios. Returns list of scenario dicts."""
    scenarios = []
    for path in sorted(CANNED_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            scenarios.append(data)
        except Exception as exc:
            logger.warning("Failed to load canned scenario %s: %s", path.name, exc)
    return scenarios


def _load_default() -> Dict[str, Any]:
    """Load tidewatch fallback unconditionally."""
    tidewatch = CANNED_DIR / "tidewatch.json"
    return json.loads(tidewatch.read_text(encoding="utf-8"))


def get_scenario(scenario_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Resolution order:
    1. If scenario_id given: search canned, then DB
    2. If _active set: return cached
    3. If DB has is_active=1: load, cache, return
    4. Else: return tidewatch default
    """
    global _active

    if scenario_id:
        # Search canned first
        for sc in list_canned():
            if sc.get("id") == scenario_id:
                with _lock:
                    _active = sc
                return sc
        # Then DB
        try:
            from backend import db
            for row in db.list_scenarios():
                if row["id"] == scenario_id:
                    sc = row["scenario"]
                    with _lock:
                        _active = sc
                    return sc
        except Exception as exc:
            logger.debug("DB lookup failed: %s", exc)
        logger.warning("Scenario %s not found, falling back to default", scenario_id)
        return _load_default()

    with _lock:
        if _active is not None:
            return _active

    # Try DB
    try:
        from backend import db
        db.init_db()
        sc = db.get_active_scenario()
        if sc:
            with _lock:
                _active = sc
            return sc
    except Exception as exc:
        logger.debug("DB active scenario lookup failed: %s", exc)

    # Default
    default = _load_default()
    with _lock:
        _active = default
    return default


def select(scenario_id: str) -> Optional[Dict[str, Any]]:
    """Set active scenario. Returns scenario dict or None if not found."""
    global _active
    sc = get_scenario(scenario_id)
    if sc.get("id") != scenario_id:
        return None
    try:
        from backend import db
        # Save to DB if not already there
        try:
            db.save_scenario(sc["id"], sc["name"], sc, _utcnow())
        except Exception:
            pass
        db.set_active_scenario(scenario_id)
    except Exception as exc:
        logger.debug("DB set_active failed: %s", exc)
    with _lock:
        _active = sc
    return sc


def seed_from_api(
    query: str,
    timeout_s: float = 4.0,
    use_acled: bool = True,
    country: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Seed scenario from GDELT + ACLED. Falls back to canned on any failure.

    Layers:
    1. GDELT events (cache-backed)
    2. ACLED events (cache-backed; optional if use_acled=True)
    3. Tension score + actor relationships from events
    4. mapping.articles_to_scenario extended with event context
    """
    try:
        from . import mapping
        from sources import gdelt_adapter, acled_adapter, tension as tension_mod

        gdelt_events = gdelt_adapter.fetch(query, timeout_s=timeout_s)
        acled_events: list = []
        if use_acled:
            acled_events = acled_adapter.fetch(query, country=country, timeout_s=timeout_s)

        # UCDP conflict history — always available via seed, enriches conflict_score
        try:
            from sources import ucdp_adapter
            ucdp_events = ucdp_adapter.fetch(query=query, country=country, timeout_s=3.0)
        except Exception as exc:
            logger.debug("UCDP fetch failed: %s", exc)
            ucdp_events = []

        all_events = gdelt_events + acled_events + ucdp_events
        # De-dup by event_id
        seen_ids: set = set()
        unique_events = []
        for ev in all_events:
            if ev.event_id not in seen_ids:
                seen_ids.add(ev.event_id)
                unique_events.append(ev)

        tension_level, actor_rels = tension_mod.score(unique_events)

        # OSM/Overpass infrastructure context — bbox derived from query/country
        try:
            from sources import overpass_adapter
            # Map query + country text to a geographic bounding box
            region_hint = f"{query} {country or ''}".strip()
            bbox = overpass_adapter.bbox_for_region(region_hint)
            if bbox:
                logger.info("Overpass: using bbox %s for region '%s'", bbox, region_hint)
            infra_records = overpass_adapter.fetch(bbox=bbox, timeout_s=6.0)
            infra_records = overpass_adapter.filter_by_criticality(infra_records, "high")
            logger.info("Overpass: %d high-criticality infra records", len(infra_records))
        except Exception as exc:
            logger.debug("Overpass fetch failed: %s", exc)
            infra_records = []

        # Build raw article list for mapping (GDELT shape — backward compat)
        articles = [
            {"title": ev.summary, "domain": ev.source, "url": ""}
            for ev in unique_events
        ]

        sc = mapping.articles_to_scenario(
            articles,
            query,
            events=unique_events,
            tension_level=tension_level,
            actor_relationships=actor_rels,
            infrastructure=infra_records,
        )
        if sc is None:
            raise ValueError("empty event list")

        sources_used = []
        if gdelt_events:
            sources_used.append("gdelt")
        if acled_events:
            sources_used.append("acled")
        if ucdp_events:
            sources_used.append("ucdp")
        sc["sources_used"] = sources_used

        try:
            from backend import db
            db.save_scenario(sc["id"], sc["name"], sc, _utcnow())
        except Exception:
            pass
        return sc
    except Exception as exc:
        logger.warning("seed_from_api failed (%s), using canned fallback", exc)
        return _load_default()
