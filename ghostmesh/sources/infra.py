"""Map free-text to infrastructure relevance tags."""
from __future__ import annotations
from typing import List

_RULES: List[tuple] = [
    (["port", "harbor", "maritime", "ship", "crane", "terminal", "container"], "port"),
    (["grid", "power", "electric", "substation", "utility", "pge", "ercot", "load-shed"], "grid"),
    (["substation", "relay", "transformer", "feeder"], "substation"),
    (["pipeline", "oil", "gas", "colonial", "lpg", "lng"], "pipeline"),
    (["water", "treatment", "chlorine", "dam", "reservoir", "utility"], "water"),
    (["bgp", "routing", "route", "peering", "tier-1", "autonomous system", "rpki"], "bgp"),
    (["telecom", "telco", "carrier", "broadband", "internet exchange", "isp"], "telecom"),
    (["scada", "ot ", "plc", "hmi", "historian", "ics", "industrial control", "modbus", "dnp3"], "grid"),
]


def tag(text: str) -> List[str]:
    """Return infrastructure relevance tags for given free text."""
    lower = text.lower()
    found = []
    for keywords, label in _RULES:
        if any(k in lower for k in keywords) and label not in found:
            found.append(label)
    return found or ["generic"]
