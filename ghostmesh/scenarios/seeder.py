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


def seed_from_api(query: str, timeout_s: float = 4.0) -> Dict[str, Any]:
    """
    Seed a scenario from GDELT + mapping. Falls back to canned on any failure.
    """
    try:
        from . import gdelt, mapping
        articles = gdelt.fetch_articles(query, timeout_s=timeout_s)
        sc = mapping.articles_to_scenario(articles, query)
        if sc is None:
            raise ValueError("empty articles")
        # Save to DB
        try:
            from backend import db
            db.save_scenario(sc["id"], sc["name"], sc, _utcnow())
        except Exception:
            pass
        return sc
    except Exception as exc:
        logger.warning("seed_from_api failed (%s), using canned fallback", exc)
        return _load_default()
