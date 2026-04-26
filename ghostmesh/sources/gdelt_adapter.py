"""GDELT Doc 2.0 adapter → normalized Event list."""
from __future__ import annotations
import logging
from typing import List

from .schemas import Event, make_event_id
from .infra import tag as infra_tag
from .cache import with_cache

logger = logging.getLogger(__name__)

# Actor hint keywords (mirrors mapping.ACTOR_MAP)
_ACTOR_HINTS = {
    "russia": "GRU-affiliated APT (Sandworm-class)",
    "russian": "GRU-affiliated APT (Sandworm-class)",
    "china": "PRC state-aligned APT (Volt Typhoon-class)",
    "chinese": "PRC state-aligned APT (Volt Typhoon-class)",
    "iran": "IRGC-affiliated APT (CyberAv3ngers-class)",
    "iranian": "IRGC-affiliated APT (CyberAv3ngers-class)",
    "north korea": "DPRK Lazarus-class actor",
    "dprk": "DPRK Lazarus-class actor",
    "lazarus": "DPRK Lazarus-class actor",
    "volt typhoon": "PRC state-aligned APT (Volt Typhoon)",
}

_EVENT_TYPE_HINTS = {
    "hack": "cyber-incident", "cyber": "cyber-incident", "breach": "cyber-incident",
    "malware": "cyber-incident", "ransomware": "cyber-incident", "attack": "armed-conflict",
    "war": "armed-conflict", "conflict": "armed-conflict", "military": "armed-conflict",
    "sanction": "diplomatic", "treaty": "diplomatic", "summit": "diplomatic",
    "protest": "protest", "riot": "protest",
}


def _classify_event_type(text: str) -> str:
    lower = text.lower()
    for kw, et in _EVENT_TYPE_HINTS.items():
        if kw in lower:
            return et
    return "other"


def _extract_actors(text: str) -> List[str]:
    lower = text.lower()
    found = []
    for kw, label in _ACTOR_HINTS.items():
        if kw in lower and label not in found:
            found.append(label)
    return found or ["Unknown actor"]


def _article_to_event(article: dict) -> Event:
    title = article.get("title", "")
    domain = article.get("domain", "")
    url = article.get("url", "")
    seen = article.get("seendate", "")
    country = article.get("sourcecountry", "")

    blob = f"{title} {domain}"
    return Event(
        event_id=make_event_id("gdelt", url or title),
        source="gdelt",
        timestamp=seen,
        location=country,
        actors=_extract_actors(blob),
        event_type=_classify_event_type(blob),
        summary=title[:280],
        tension_weight=0.0,  # set by tension.py downstream
        infrastructure_relevance=infra_tag(blob),
    )


def fetch(query: str, timeout_s: float = 5.0) -> List[Event]:
    """
    Fetch GDELT events for query. Cache-backed. Returns Event list — never raises.
    """
    def _live() -> List[dict]:
        from scenarios.gdelt import fetch_articles
        articles = fetch_articles(query, timeout_s=timeout_s, max_records=25)
        return articles

    raw = with_cache("gdelt", query, fetcher=_live)
    events = []
    for item in raw:
        try:
            events.append(_article_to_event(item))
        except Exception as exc:
            logger.debug("gdelt event parse error: %s", exc)
    return events
