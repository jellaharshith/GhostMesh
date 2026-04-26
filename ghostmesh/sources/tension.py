"""Compute tension score and actor relationships from a list of Events."""
from __future__ import annotations
import math
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from .schemas import Event

_TYPE_WEIGHT: Dict[str, float] = {
    "armed-conflict":  0.90,
    "cyber-incident":  0.80,
    "protest":         0.40,
    "diplomatic":      0.30,
    "other":           0.20,
}

_HOSTILE_TYPES = {"armed-conflict", "cyber-incident"}


def _days_old(ts: str) -> float:
    if not ts:
        return 30.0
    for fmt in ("%Y%m%dT%H%M%SZ", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y%m%d"):
        try:
            dt = datetime.strptime(ts, fmt).replace(tzinfo=timezone.utc)
            delta = datetime.now(timezone.utc) - dt
            return max(0.0, delta.total_seconds() / 86400.0)
        except ValueError:
            continue
    return 30.0


def score(events: List[Event]) -> Tuple[float, List[Dict[str, str]]]:
    """
    Returns (tension_level [0..1], actor_relationships).
    tension_level: recency-decayed mean of event type weights.
    actor_relationships: list of {actor_a, actor_b, posture}.
    """
    if not events:
        return 0.0, []

    weighted: List[float] = []
    for ev in events:
        base = _TYPE_WEIGHT.get(ev.event_type, 0.20)
        decay = 0.85 ** _days_old(ev.timestamp)
        weighted.append(base * decay)

    # Top-10 events drive the score
    top = sorted(weighted, reverse=True)[:10]
    tension = round(sum(top) / len(top), 3) if top else 0.0

    # Actor relationships: pair actors that co-occur in same event
    seen: Dict[Tuple[str, str], str] = {}
    for ev in events:
        actors = ev.actors
        posture = "hostile" if ev.event_type in _HOSTILE_TYPES else "tension"
        for i, a in enumerate(actors):
            for b in actors[i + 1:]:
                key = (min(a, b), max(a, b))
                # hostile beats tension once seen
                if seen.get(key) != "hostile":
                    seen[key] = posture

    relationships = [
        {"actor_a": k[0], "actor_b": k[1], "posture": v}
        for k, v in seen.items()
    ]

    return tension, relationships
