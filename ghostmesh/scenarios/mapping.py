"""Map GDELT articles to a normalized Scenario dict."""
from __future__ import annotations
import hashlib
from typing import Any, Dict, List, Optional, Tuple

INFRA_PRESETS: Dict[str, Tuple[str, List[Dict[str, str]]]] = {
    "port": (
        "Container port terminal SCADA",
        [
            {"name": "TOS-SRV-01", "type": "Terminal Operating System Server", "status": "at-risk"},
            {"name": "CRANE-PLC-01", "type": "Crane Control PLC", "status": "at-risk"},
            {"name": "HMI-PORT-01", "type": "Port Operations HMI", "status": "at-risk"},
            {"name": "SCADA-FW", "type": "SCADA Firewall", "status": "online"},
        ],
    ),
    "grid": (
        "Power grid SCADA / substation control",
        [
            {"name": "RTU-MAIN", "type": "Remote Terminal Unit", "status": "at-risk"},
            {"name": "HMI-SUB-01", "type": "Substation HMI", "status": "at-risk"},
            {"name": "HISTORIAN-GRID", "type": "Grid Historian", "status": "at-risk"},
            {"name": "IT-OT-FW", "type": "IT/OT Boundary Firewall", "status": "online"},
        ],
    ),
    "substation": (
        "Power grid SCADA / substation control",
        [
            {"name": "RTU-MAIN", "type": "Remote Terminal Unit", "status": "at-risk"},
            {"name": "HMI-SUB-01", "type": "Substation HMI", "status": "at-risk"},
            {"name": "HISTORIAN-GRID", "type": "Grid Historian", "status": "at-risk"},
            {"name": "IT-OT-FW", "type": "IT/OT Boundary Firewall", "status": "online"},
        ],
    ),
    "pipeline": (
        "Pipeline SCADA / OT network",
        [
            {"name": "SCADA-SRV-01", "type": "SCADA Server", "status": "at-risk"},
            {"name": "RTU-PIPELINE", "type": "Pipeline RTU", "status": "at-risk"},
            {"name": "HMI-PIPE-01", "type": "Pipeline HMI", "status": "at-risk"},
            {"name": "FW-OT", "type": "OT Firewall", "status": "online"},
        ],
    ),
    "water": (
        "Water utility OT / treatment plant",
        [
            {"name": "HMI-WATER-01", "type": "Water Treatment HMI", "status": "at-risk"},
            {"name": "PLC-CHEM-01", "type": "Chemical Dosing PLC", "status": "at-risk"},
            {"name": "HIST-WATER", "type": "Water SCADA Historian", "status": "at-risk"},
            {"name": "FW-OT", "type": "OT Firewall", "status": "online"},
        ],
    ),
    "bgp": (
        "Telecom BGP routing infrastructure",
        [
            {"name": "RR-CORE-01", "type": "BGP Route Reflector", "status": "at-risk"},
            {"name": "PEERING-RTR-01", "type": "Peering Router", "status": "at-risk"},
            {"name": "NMS-SERVER", "type": "Network Management System", "status": "at-risk"},
            {"name": "RPKI-VALIDATOR", "type": "RPKI Validation Server", "status": "at-risk"},
        ],
    ),
    "telecom": (
        "Telecom network management infrastructure",
        [
            {"name": "NMS-SERVER", "type": "Network Management System", "status": "at-risk"},
            {"name": "PEERING-RTR-01", "type": "Peering Router", "status": "at-risk"},
            {"name": "MGMT-VPN", "type": "Management VPN", "status": "at-risk"},
            {"name": "FW-MGMT", "type": "Management Firewall", "status": "online"},
        ],
    ),
}

DEFAULT_INFRA = (
    "Generic OT / critical infrastructure network",
    [
        {"name": "SCADA-SRV-01", "type": "SCADA Server", "status": "at-risk"},
        {"name": "HMI-01", "type": "HMI", "status": "at-risk"},
        {"name": "HIST-01", "type": "Historian", "status": "at-risk"},
        {"name": "FW-OT", "type": "OT Firewall", "status": "online"},
    ],
)

ACTOR_MAP: Dict[str, str] = {
    "russia": "GRU-affiliated APT (Sandworm-class)",
    "russian": "GRU-affiliated APT (Sandworm-class)",
    "china": "PRC state-aligned APT (Volt Typhoon-class)",
    "chinese": "PRC state-aligned APT (Volt Typhoon-class)",
    "volt typhoon": "PRC state-aligned APT (Volt Typhoon)",
    "iran": "IRGC-affiliated APT (CyberAv3ngers-class)",
    "iranian": "IRGC-affiliated APT (CyberAv3ngers-class)",
    "north korea": "DPRK Lazarus-class actor",
    "dprk": "DPRK Lazarus-class actor",
    "lazarus": "DPRK Lazarus-class actor",
}

_CODENAMES = [
    "Ironwood", "Tidewave", "Shadowgrid", "Blackmesh", "Frostline",
    "Darkwater", "Steelgate", "Vortex", "Phantom", "Greystone",
]


def _codename(query: str) -> str:
    idx = int(hashlib.sha1(query.encode()).hexdigest(), 16) % len(_CODENAMES)
    return _CODENAMES[idx]


def _first_infra(blob: str) -> Tuple[str, List[Dict[str, str]]]:
    for kw, preset in INFRA_PRESETS.items():
        if kw in blob:
            return preset
    return DEFAULT_INFRA


def _first_actor(blob: str) -> Optional[str]:
    for kw, label in ACTOR_MAP.items():
        if kw in blob:
            return label
    return None


def articles_to_scenario(
    articles: List[Dict[str, Any]],
    query: str,
) -> Optional[Dict[str, Any]]:
    """
    Project GDELT articles + query into a Scenario dict.
    Returns None if articles list is empty.
    """
    if not articles:
        return None

    blob = " ".join(
        (a.get("title", "") + " " + a.get("domain", "")).lower()
        for a in articles
    )

    infra_label, assets = _first_infra(blob)
    actor = _first_actor(blob) or "Unattributed advanced persistent threat"

    top_titles = [a.get("title", "") for a in articles[:3] if a.get("title")]
    brief_suffix = " ".join(f'Recent reporting: "{t}".' for t in top_titles[:2])

    sid = "seeded-" + hashlib.sha1((query + blob[:200]).encode()).hexdigest()[:8]

    return {
        "id": sid,
        "name": f"Operation {_codename(query)}",
        "brief": (
            f"{actor} has been observed conducting cyber operations targeting {infra_label}. "
            f"Threat intelligence derived from recent open-source reporting. {brief_suffix} "
            "Blue Team must assess the threat and develop a defensive response."
        ),
        "blue_objectives": [
            f"Assess and contain threat to {infra_label}",
            "Identify adversary TTPs and initial access vector",
            "Evict actor while maintaining operational continuity",
            "Preserve evidence for attribution and coordination",
        ],
        "red_posture": (
            f"{actor} conducting reconnaissance and pre-positioning against {infra_label}. "
            "Threat derived from OSINT — exact foothold unknown. Assume persistence capability. "
            "Escalation authority: disruption of primary operations."
        ),
        "assets": assets,
    }
