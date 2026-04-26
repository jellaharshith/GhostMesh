"""Scenario seeder: canned scenarios + optional GDELT-seeded scenarios."""
from __future__ import annotations
import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Per-scenario GDELT query strings for live intel enrichment.
# Keyed by scenario id prefix (matched via startswith).
_SCENARIO_QUERIES: Dict[str, Dict[str, str]] = {
    "port-cyber": {
        "query": "container port SCADA cyber attack critical infrastructure",
        "country": "United States",
    },
    "tidewatch": {
        "query": "power grid SCADA cyber attack critical infrastructure APT",
        "country": "United States",
    },
    "grid-substation": {
        "query": "power substation SCADA cyber attack grid disruption",
        "country": "United States",
    },
    "regional-grid": {
        "query": "power grid regional cyber threat SCADA ICS",
        "country": "United States",
    },
    "baltic-grid": {
        "query": "Baltic power grid cyber attack substation NATO",
        "country": "Estonia",
    },
    "telecom-bgp": {
        "query": "BGP route hijack telecom cyber attack ISP infrastructure",
        "country": "United States",
    },
}

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


def _intel_query_for(scenario_id: str, sc: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, str]]:
    """Return GDELT enrichment query params for a scenario id, or derive from scenario name/brief."""
    for prefix, params in _SCENARIO_QUERIES.items():
        if scenario_id.startswith(prefix):
            return params
    # Fallback: derive a query from the scenario name or brief
    if sc:
        name = sc.get("name", "")
        brief = sc.get("brief", "")[:200]
        if name or brief:
            return {"query": f"{name} {brief[:80]}".strip(), "country": "United States"}
    return None


def _enrich_canned(sc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Overlay live GDELT/OSM intel onto a canned scenario dict.

    Fetches only the intel fields (tension_score, conflict_score,
    infrastructure_risk_score, adversary_aggression_score, scenario_summary,
    doctrine_notes, strategic_notes, infrastructure, recent_events,
    recommended_red_posture) from a live seed, then merges them into the
    canned scenario's core fields (id, name, brief, blue_objectives,
    red_posture, assets) which are never overwritten.

    Silent on any failure — returns the original sc unchanged.
    """
    intel_params = _intel_query_for(sc.get("id", ""), sc)
    if not intel_params:
        return sc
    try:
        enriched = seed_from_api(
            query=intel_params["query"],
            timeout_s=5.0,
            country=intel_params.get("country"),
        )
        intel_keys = [
            "tension_level", "tension_score", "conflict_score",
            "infrastructure_risk_score", "adversary_aggression_score",
            "scenario_summary", "doctrine_notes", "strategic_notes",
            "infrastructure", "recent_events", "actor_relationships",
            "recommended_red_posture", "sources_used",
            "historical_baseline", "terrain",
        ]
        merged = dict(sc)
        # Preserve immutable user-authored brief/query metadata.
        merged["user_brief"] = sc.get("user_brief") or sc.get("brief", "")
        merged["scenario_query"] = sc.get("scenario_query") or merged.get("user_brief", "")
        for k in intel_keys:
            if k in enriched:
                merged[k] = enriched[k]
        return merged
    except Exception as exc:
        logger.debug("_enrich_canned failed for %s: %s", sc.get("id"), exc)
        return sc


def select(scenario_id: str) -> Optional[Dict[str, Any]]:
    """Set active scenario. Returns scenario dict or None if not found."""
    global _active
    sc = get_scenario(scenario_id)
    if sc.get("id") != scenario_id:
        return None

    # Auto-enrich canned scenarios with live GDELT/OSM intel.
    # Only enrich if the scenario lacks intel fields (i.e. is a bare canned file).
    if not sc.get("tension_score") and not sc.get("recent_events"):
        sc = _enrich_canned(sc)

    try:
        from backend import db
        try:
            db.save_scenario(sc["id"], sc["name"], sc, _utcnow())
        except Exception:
            pass
        db.set_active_scenario(sc["id"])
    except Exception as exc:
        logger.debug("DB set_active failed: %s", exc)
    with _lock:
        _active = sc
    return sc


def seed_from_api(
    query: str,
    timeout_s: float = 4.0,
    country: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Seed scenario from a fused live + historical + geospatial feed.

    Layers (each one cache-backed and silent on failure):
      - GDELT 2.1 (live news events)
      - LiveUAMap (live conflict markers)
      - UCDP GED (recent armed-conflict baseline)
      - GTD (historical decade-baseline, attached as ``historical_baseline``)
      - Overpass / OSM (high-criticality infrastructure)
      - OpenTopography SRTM (terrain summary, attached as ``terrain``)
    """
    global _active
    try:
        from . import mapping
        from sources import gdelt_adapter, tension as tension_mod

        gdelt_events = gdelt_adapter.fetch(query, timeout_s=timeout_s)

        # LiveUAMap — primary live conflict marker source
        try:
            from sources import liveuamap_adapter
            region_hint = f"{query} {country or ''}".strip()
            lum_bbox = None
            try:
                from sources import overpass_adapter as _ov
                lum_bbox = _ov.bbox_for_region(region_hint) if region_hint else None
            except Exception:
                lum_bbox = None
            liveua_events = liveuamap_adapter.fetch(
                bbox=lum_bbox,
                query=query,
                timeout_s=timeout_s,
            )
        except Exception as exc:
            logger.debug("LiveUAMap fetch failed: %s", exc)
            liveua_events = []

        # UCDP conflict history — enriches conflict_score
        try:
            from sources import ucdp_adapter
            ucdp_events = ucdp_adapter.fetch(query=query, country=country, timeout_s=3.0)
        except Exception as exc:
            logger.debug("UCDP fetch failed: %s", exc)
            ucdp_events = []

        all_events = gdelt_events + liveua_events + ucdp_events
        # De-dup by event_id
        seen_ids: set = set()
        unique_events = []
        for ev in all_events:
            if ev.event_id not in seen_ids:
                seen_ids.add(ev.event_id)
                unique_events.append(ev)

        tension_level, actor_rels = tension_mod.score(unique_events)

        # OSM/Overpass infrastructure context — bbox derived from query/country
        bbox: Optional[str] = None
        try:
            from sources import overpass_adapter
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

        # GTD historical baseline — recent decade in the same theater
        try:
            from sources import gtd_adapter
            historical_baseline = gtd_adapter.recent_decade(
                region=(country or query), limit=20
            )
        except Exception as exc:
            logger.debug("GTD fetch failed: %s", exc)
            historical_baseline = []

        # OpenTopography SRTM terrain summary
        try:
            from sources import opentopography_adapter
            terrain = opentopography_adapter.summarize(
                region=(country or query), bbox=bbox
            )
        except Exception as exc:
            logger.debug("OpenTopography fetch failed: %s", exc)
            terrain = {}

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

        # Immutable source-of-truth text that frontend should always render.
        sc["user_brief"] = query.strip()
        sc["scenario_query"] = query.strip()

        # Attach the new enrichment blocks
        if historical_baseline:
            sc["historical_baseline"] = [
                {
                    "event_id":   ev.event_id,
                    "timestamp":  ev.timestamp,
                    "location":   ev.location,
                    "actors":     ev.actors,
                    "event_type": ev.event_type,
                    "summary":    ev.summary,
                }
                for ev in historical_baseline
            ]
        if terrain:
            sc["terrain"] = terrain

        sources_used = []
        if gdelt_events:
            sources_used.append("gdelt")
        if liveua_events:
            sources_used.append("liveuamap")
        if ucdp_events:
            sources_used.append("ucdp")
        if historical_baseline:
            sources_used.append("gtd")
        if terrain:
            sources_used.append("opentopography")
        sc["sources_used"] = sources_used

        try:
            from backend import db
            db.save_scenario(sc["id"], sc["name"], sc, _utcnow())
            db.set_active_scenario(sc["id"])
        except Exception:
            pass
        with _lock:
            _active = sc
        return sc
    except Exception as exc:
        logger.warning("seed_from_api failed (%s), using canned fallback", exc)
        return _load_default()
