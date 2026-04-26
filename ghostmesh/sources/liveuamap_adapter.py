"""LiveUAMap adapter → normalized Event list.

LiveUAMap publishes near-real-time geolocated conflict event markers.  Their
public time/region JSON endpoint requires no authentication but is rate-limited.
We hit it through ``with_cache(...)`` so a single fetch satisfies subsequent
calls for 24 hours, and degrade silently to a committed seed sample.

Never raises into the request path.
"""
from __future__ import annotations
import logging
from typing import List, Optional

import requests

from .schemas import Event, make_event_id
from .infra import tag as infra_tag
from .cache import with_cache

logger = logging.getLogger(__name__)

LIVEUAMAP_URL = "https://liveuamap.com/api/getmarkers"

# Heuristic icon/marker → normalized event_type
_MARKER_TYPE_MAP = {
    "shoot":   "armed-conflict",
    "fire":    "armed-conflict",
    "fight":   "armed-conflict",
    "explos":  "armed-conflict",
    "bomb":    "armed-conflict",
    "missile": "armed-conflict",
    "drone":   "armed-conflict",
    "tank":    "armed-conflict",
    "artill":  "armed-conflict",
    "cyber":   "cyber-incident",
    "hack":    "cyber-incident",
    "protest": "protest",
    "riot":    "protest",
    "summit":  "diplomatic",
    "treaty":  "diplomatic",
    "diplom":  "diplomatic",
}


def _classify(text: str) -> str:
    lower = (text or "").lower()
    for kw, et in _MARKER_TYPE_MAP.items():
        if kw in lower:
            return et
    return "other"


def _row_to_event(row: dict) -> Event:
    """Normalize one LiveUAMap marker row.

    Tolerant to schema drift — LiveUAMap's marker JSON uses lowercase keys but
    has changed shape several times over the years.
    """
    marker_id = str(row.get("id") or row.get("marker_id") or "")
    title = (row.get("title") or row.get("name") or "").strip()
    desc = (row.get("description") or row.get("html") or row.get("text") or "").strip()
    desc_short = desc[:280]
    timestamp = row.get("date") or row.get("time") or row.get("created_at") or ""
    country = (row.get("country") or row.get("region") or "").strip()
    place = (row.get("place") or row.get("city") or "").strip()
    location = ", ".join(p for p in [place, country] if p) or "Unknown"

    icon = (row.get("picsource") or row.get("icon") or "").lower()
    event_type = _classify(f"{icon} {title} {desc_short}")

    # Extract actors heuristically: LiveUAMap rarely tags actors; pull obvious ones
    actors: List[str] = []
    blob = f"{title} {desc_short}".lower()
    for kw, label in [
        ("russian",  "Russian forces"),
        ("ukrainian", "Ukrainian forces"),
        ("ukraine",  "Ukrainian forces"),
        ("israeli",  "Israeli forces"),
        ("hamas",    "Hamas"),
        ("hezbollah", "Hezbollah"),
        ("houthi",   "Houthi forces"),
        ("isis",     "ISIS-affiliated"),
        ("iranian",  "Iranian forces"),
        ("us ",      "US forces"),
        ("nato",     "NATO forces"),
    ]:
        if kw in blob and label not in actors:
            actors.append(label)

    summary = title or desc_short or f"LiveUAMap event in {location}"

    return Event(
        event_id=make_event_id("liveuamap", marker_id or summary),
        source="liveuamap",
        timestamp=timestamp,
        location=location,
        actors=actors or ["Unattributed"],
        event_type=event_type,
        summary=summary[:280],
        tension_weight=0.0,
        infrastructure_relevance=infra_tag(f"{title} {desc_short}"),
    )


def fetch(
    query: Optional[str] = None,
    bbox: Optional[str] = None,
    hours: int = 72,
    limit: int = 40,
    timeout_s: float = 5.0,
) -> List[Event]:
    """
    Fetch LiveUAMap markers near a query/bbox.

    bbox format mirrors Overpass: "south,west,north,east".  When supplied the
    public endpoint is queried with explicit lat/lon bounds; otherwise we pull
    the global recent feed and filter client-side by ``query`` substring.
    Cache-backed; never raises.
    """
    cache_key = f"{query or ''}:{bbox or ''}:{hours}"

    def _live() -> List[dict]:
        params: dict = {"format": "json", "limit": limit}
        if bbox:
            try:
                south, west, north, east = (float(x) for x in bbox.split(","))
                params.update({
                    "south": south, "west": west,
                    "north": north, "east": east,
                })
            except Exception:
                pass
        # LiveUAMap exposes a "since" parameter as a unix epoch
        try:
            import time
            params["since"] = int(time.time() - hours * 3600)
        except Exception:
            pass

        resp = requests.get(
            LIVEUAMAP_URL,
            params=params,
            timeout=timeout_s,
            headers={"User-Agent": "GhostMesh/1.0 (+research)"},
        )
        resp.raise_for_status()
        body = resp.json()
        # LiveUAMap returns either a top-level list or {"markers": [...]} depending on version
        if isinstance(body, list):
            return body
        return body.get("markers") or body.get("data") or []

    raw = with_cache("liveuamap", cache_key, fetcher=_live)

    events: List[Event] = []
    q_lower = (query or "").lower()
    for row in raw:
        try:
            ev = _row_to_event(row)
        except Exception as exc:
            logger.debug("liveuamap row parse error: %s", exc)
            continue
        # Optional client-side query filter (when no bbox-narrowed pull)
        if q_lower and bbox is None:
            blob = f"{ev.summary} {ev.location} {' '.join(ev.actors)}".lower()
            if q_lower not in blob:
                continue
        events.append(ev)

    return events[:limit]
