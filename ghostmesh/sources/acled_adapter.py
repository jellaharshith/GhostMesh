"""ACLED API adapter → normalized Event list.

Live API requires ACLED_EMAIL + ACLED_KEY env vars.
Falls back to disk cache then data/seed/acled_sample.json if unavailable.
"""
from __future__ import annotations
import logging
import os
from typing import List, Optional

import requests

from .schemas import Event, make_event_id
from .infra import tag as infra_tag
from .cache import with_cache

logger = logging.getLogger(__name__)

ACLED_URL = "https://api.acleddata.com/acled/read"

_EVENT_TYPE_MAP = {
    "battles":                         "armed-conflict",
    "explosions/remote violence":       "armed-conflict",
    "violence against civilians":       "armed-conflict",
    "protests":                         "protest",
    "riots":                            "protest",
    "strategic developments":           "diplomatic",
}


def _acled_row_to_event(row: dict) -> Event:
    event_date = row.get("event_date", "")
    country = row.get("country", "")
    admin1 = row.get("admin1", "")
    location = f"{admin1}, {country}".strip(", ")
    actor1 = row.get("actor1", "")
    actor2 = row.get("actor2", "")
    actors = [a for a in [actor1, actor2] if a]
    raw_type = row.get("event_type", "other").lower()
    event_type = _EVENT_TYPE_MAP.get(raw_type, "other")
    notes = row.get("notes", "")[:280]
    key = row.get("data_id", "") or (event_date + actor1 + country)
    return Event(
        event_id=make_event_id("acled", key),
        source="acled",
        timestamp=event_date,
        location=location,
        actors=actors,
        event_type=event_type,
        summary=notes or f"{event_type} — {location}",
        tension_weight=0.0,
        infrastructure_relevance=infra_tag(notes + " " + raw_type),
    )


def fetch(
    query: str,
    country: Optional[str] = None,
    limit: int = 25,
    timeout_s: float = 6.0,
) -> List[Event]:
    """
    Fetch ACLED events. Needs ACLED_EMAIL + ACLED_KEY env vars for live fetch.
    Cache-backed; never raises.
    """
    email = os.getenv("ACLED_EMAIL", "")
    key_env = os.getenv("ACLED_KEY", "")
    cache_key = f"{query}:{country or ''}"

    def _live() -> List[dict]:
        if not email or not key_env:
            raise RuntimeError("ACLED_EMAIL / ACLED_KEY not set")
        params: dict = {
            "email": email,
            "key": key_env,
            "limit": limit,
            "fields": "data_id|event_date|country|admin1|event_type|actor1|actor2|notes",
            "format": "json",
        }
        if country:
            params["country"] = country
        if query:
            params["keyword"] = query
        resp = requests.get(ACLED_URL, params=params, timeout=timeout_s)
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", []) or []

    raw = with_cache("acled", cache_key, fetcher=_live)
    events = []
    for row in raw:
        try:
            events.append(_acled_row_to_event(row))
        except Exception as exc:
            logger.debug("acled row parse error: %s", exc)
    return events
