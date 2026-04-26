"""Normalized event schema shared by all source adapters."""
from __future__ import annotations
import hashlib
from dataclasses import dataclass, field
from typing import List


@dataclass
class Event:
    event_id: str
    source: str                          # gdelt | liveuamap | ucdp | gtd | local
    timestamp: str                       # ISO-8601 UTC
    location: str
    actors: List[str]
    event_type: str
    summary: str
    tension_weight: float                # 0..1
    infrastructure_relevance: List[str]  # port|grid|pipeline|water|telecom|bgp|substation|generic

    def to_dict(self) -> dict:
        return {
            "event_id":                 self.event_id,
            "source":                   self.source,
            "timestamp":                self.timestamp,
            "location":                 self.location,
            "actors":                   self.actors,
            "event_type":               self.event_type,
            "summary":                  self.summary,
            "tension_weight":           self.tension_weight,
            "infrastructure_relevance": self.infrastructure_relevance,
        }

    @staticmethod
    def from_dict(d: dict) -> "Event":
        return Event(
            event_id=d.get("event_id", ""),
            source=d.get("source", "local"),
            timestamp=d.get("timestamp", ""),
            location=d.get("location", ""),
            actors=d.get("actors", []),
            event_type=d.get("event_type", "other"),
            summary=d.get("summary", ""),
            tension_weight=float(d.get("tension_weight", 0.0)),
            infrastructure_relevance=d.get("infrastructure_relevance", ["generic"]),
        )


def make_event_id(source: str, key: str) -> str:
    return source + "-" + hashlib.sha1(key.encode()).hexdigest()[:10]
