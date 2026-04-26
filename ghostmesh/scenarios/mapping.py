"""Map fused OSINT events (GDELT / LiveUAMap / UCDP / GTD) to a normalized Scenario dict."""
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


def _tension_score_int(tension_level: float) -> int:
    """Convert 0–1 float tension to 0–100 display integer."""
    return min(100, max(0, round(tension_level * 100)))


def _conflict_score(events: List[Any]) -> int:
    """Count armed-conflict events → 0–100 intensity."""
    if not events:
        return 0
    count = sum(
        1 for ev in events
        if (ev.event_type if hasattr(ev, "event_type") else ev.get("event_type", "")) == "armed-conflict"
    )
    return min(100, round(count / max(1, len(events)) * 100 + count * 8))


def _infra_risk_score(events: List[Any]) -> int:
    """Estimate infrastructure risk from events with infra_relevance tags."""
    if not events:
        return 0
    tagged = sum(
        1 for ev in events
        if (ev.infrastructure_relevance if hasattr(ev, "infrastructure_relevance") else ev.get("infrastructure_relevance", []))
    )
    return min(100, round(tagged / max(1, len(events)) * 100 + tagged * 5))


def _aggression_score(tension_level: float, conflict_score: int) -> int:
    return min(100, round((tension_level * 60 + conflict_score * 0.4)))


def _retrieval_csis_notes(actor: str, infra_label: str) -> List[str]:
    """Query Chroma retrieval service for CSIS-style strategic analysis. Never raises."""
    try:
        from retrieval.service import retrieve
        query = f"{actor} strategic implications infrastructure escalation geopolitical"
        snips = retrieve(query, k=2, tags=["csis", "analysis"])
        return [f"{s['source']}: {s['text'][:200]}" for s in snips if s.get("text")]
    except Exception:
        return []


def _retrieval_doctrine_notes(actor: str, infra_label: str) -> List[str]:
    """Query Chroma retrieval service for doctrine-grounded notes. Never raises."""
    try:
        from retrieval.service import retrieve
        query = f"{actor} critical infrastructure cyberspace operations doctrine posture"
        snips = retrieve(query, k=3, tags=["doctrine", "jcs"])
        return [f"{s['source']}: {s['text'][:200]}" for s in snips if s.get("text")]
    except Exception:
        return []


def _doctrine_notes(actor: str, tension_level: float, infra_label: str) -> List[str]:
    """Generate Joint-doctrine-grounded observations based on actor and tension level."""
    notes = []
    actor_lower = actor.lower()
    if "prc" in actor_lower or "volt" in actor_lower or "china" in actor_lower:
        notes.append(
            "Joint Pub 3-12 (Cyberspace Ops): PRC doctrine emphasizes pre-conflict access "
            "to critical infrastructure for strategic deterrence — consistent with observed pre-positioning."
        )
        notes.append(
            "CJCS assessment: Volt Typhoon-class actors prioritize persistence over immediate effect; "
            "expect long dwell time before activation."
        )
    elif "gru" in actor_lower or "sandworm" in actor_lower or "russia" in actor_lower:
        notes.append(
            "Joint Pub 3-12: Russian doctrine integrates cyber effects with kinetic operations "
            "(Gerasimov framework) — infrastructure disruption timed to diplomatic crisis windows."
        )
        notes.append(
            "CJCS warning: Sandworm-class actors demonstrated grid-disruption capability (Industroyer/CRASHOVERRIDE); "
            "OT network segmentation is priority countermeasure."
        )
    elif "irgc" in actor_lower or "iran" in actor_lower or "cyberav" in actor_lower:
        notes.append(
            "Joint Pub 3-12: IRGC cyber doctrine uses ICS/SCADA targeting as asymmetric retaliation "
            "tool against US partners in response to sanctions or kinetic pressure."
        )
    elif "dprk" in actor_lower or "lazarus" in actor_lower:
        notes.append(
            "Joint Pub 3-12: DPRK Lazarus operations prioritize financial disruption and intelligence "
            "collection — critical infrastructure targeting signals escalation to strategic level."
        )
    else:
        notes.append(
            "Joint Pub 3-12 (Cyberspace Ops): Unattributed actor consistent with Tier-2 state-sponsored "
            "capability — lateral movement from IT to OT boundary is primary threat vector."
        )

    if tension_level >= 0.70:
        notes.append(
            f"JP 5-0 (Joint Planning): High tension environment ({tension_level:.0%}) warrants "
            f"increased readiness posture — defensive cyber operations priority elevated."
        )
    elif tension_level >= 0.40:
        notes.append(
            f"JP 5-0: Elevated tension indicators ({tension_level:.0%}) suggest adversary is in "
            f"pre-conflict access phase — anticipate escalation within 30–90 day window."
        )

    return notes


def _strategic_notes(actor: str, infra_label: str, tension_level: float) -> List[str]:
    """CSIS-style strategic framing for scenario context."""
    notes = []
    actor_lower = actor.lower()

    if "prc" in actor_lower or "volt" in actor_lower:
        notes.append(
            "CSIS Assessment: PRC critical infrastructure pre-positioning represents strategic "
            "leverage — activating disruption capabilities during Taiwan crisis is a declared "
            "Chinese deterrence option per PLA strategic doctrine."
        )
    elif "gru" in actor_lower or "russia" in actor_lower:
        notes.append(
            "CSIS Assessment: Russian infrastructure operations in NATO context follow a "
            "graduated escalation model — cyber disruption precedes kinetic action as a "
            "conflict preparation mechanism (Gerasimov doctrine, updated 2019)."
        )
    elif "irgc" in actor_lower or "iran" in actor_lower:
        notes.append(
            "CSIS Assessment: Iranian cyber operations against US critical infrastructure "
            "escalated significantly post-2022. IRGC-linked groups have demonstrated "
            "ICS/SCADA manipulation capability at operational level."
        )
    else:
        notes.append(
            "CSIS Assessment: Unattributed intrusion into critical infrastructure warrants "
            "assumption of state-nexus capability — non-state actors rarely achieve persistent "
            "OT network access without nation-state technical support."
        )

    notes.append(
        f"Strategic risk: {infra_label} disruption in current geopolitical environment "
        f"could trigger cascading economic effects across allied supply chains. "
        f"Escalation management requires coordinated interagency response."
    )
    return notes


def _scenario_summary(
    actor: str,
    infra_label: str,
    tension_level: float,
    events: List[Any],
    query: str,
) -> str:
    """Generate a clean narrative paragraph summarizing the scenario intelligence picture."""
    tension_word = (
        "critical" if tension_level >= 0.70
        else "elevated" if tension_level >= 0.40
        else "moderate"
    )
    event_count = len(events)
    conflict_events = [
        ev for ev in events
        if (ev.event_type if hasattr(ev, "event_type") else ev.get("event_type", "")) == "armed-conflict"
    ]
    cyber_events = [
        ev for ev in events
        if (ev.event_type if hasattr(ev, "event_type") else ev.get("event_type", "")) == "cyber-incident"
    ]
    parts = [
        f"Intelligence fusion across {event_count} open-source events indicates a {tension_word} "
        f"threat environment associated with query \"{query}\"."
    ]
    if actor and "unattributed" not in actor.lower():
        parts.append(
            f"Primary adversary assessed as {actor}, with observed activity targeting {infra_label}."
        )
    if cyber_events:
        parts.append(
            f"{len(cyber_events)} cyber-incident indicator(s) identified in the reporting window, "
            f"suggesting active intrusion operations against digital infrastructure."
        )
    if conflict_events:
        parts.append(
            f"{len(conflict_events)} armed-conflict event(s) in the regional environment "
            f"elevate the risk of cyber-kinetic coordination."
        )
    parts.append(
        "Red Cell posture is assessed as pre-positioning for disruptive operations. "
        "Blue Team priority: detect and evict before actor achieves Stage 7 (ICS impact)."
    )
    return " ".join(parts)


def _recommended_red_posture(tension_level: float, conflict_score: int) -> str:
    if tension_level >= 0.70 or conflict_score >= 60:
        return "aggressive"
    elif tension_level >= 0.40 or conflict_score >= 30:
        return "opportunistic"
    else:
        return "conservative"


def articles_to_scenario(
    articles: List[Dict[str, Any]],
    query: str,
    events: Optional[List[Any]] = None,
    tension_level: float = 0.0,
    actor_relationships: Optional[List[Dict[str, str]]] = None,
    infrastructure: Optional[List[Dict[str, Any]]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Project articles/events + query into a Scenario dict.
    Returns None if both articles and events are empty.

    events: optional list of sources.schemas.Event objects (or dicts).
    tension_level: pre-computed tension score [0..1].
    actor_relationships: list of {actor_a, actor_b, posture} dicts.
    """
    if not articles and not events:
        return None

    blob = " ".join(
        (a.get("title", "") + " " + a.get("domain", "")).lower()
        for a in articles
    )
    query_blob = (query or "").lower()
    if query_blob:
        # Ensure user-provided scenario text directly shapes actor/infra inference.
        blob += " " + query_blob

    # Augment blob with event summaries for better infra/actor detection
    if events:
        for ev in events:
            summary = ev.summary if hasattr(ev, "summary") else ev.get("summary", "")
            blob += " " + summary.lower()

    infra_label, assets = _first_infra(blob)

    # Actor from events first (more specific), then blob keyword scan
    actor = None
    if events:
        for ev in events:
            ev_actors = ev.actors if hasattr(ev, "actors") else ev.get("actors", [])
            for a in ev_actors:
                if a and "unknown" not in a.lower():
                    actor = a
                    break
            if actor:
                break
    actor = actor or _first_actor(blob) or "Unattributed advanced persistent threat"

    top_titles = [a.get("title", "") for a in articles[:3] if a.get("title")]
    brief_suffix = " ".join(f'Recent reporting: "{t}".' for t in top_titles[:2])

    # Tension framing
    tension_desc = ""
    if tension_level >= 0.70:
        tension_desc = "Regional tension is HIGH — geopolitical escalation indicators active. "
    elif tension_level >= 0.40:
        tension_desc = "Regional tension is ELEVATED based on recent OSINT. "

    sid = "seeded-" + hashlib.sha1((query + blob[:200]).encode()).hexdigest()[:8]

    # Top 8 recent events as dicts for schema attachment
    recent_events_dicts = []
    if events:
        for ev in events[:8]:
            if hasattr(ev, "to_dict"):
                recent_events_dicts.append(ev.to_dict())
            elif isinstance(ev, dict):
                recent_events_dicts.append(ev)

    t_score = _tension_score_int(tension_level)
    c_score = _conflict_score(events or [])
    i_score = _infra_risk_score(events or [])
    agg_score = _aggression_score(tension_level, c_score)
    red_posture_label = _recommended_red_posture(tension_level, c_score)

    # Combine static actor-keyed notes with live Chroma retrieval
    # Combine static actor-keyed notes with live Chroma retrieval
    static_doctrine = _doctrine_notes(actor, tension_level, infra_label)
    live_doctrine = _retrieval_doctrine_notes(actor, infra_label)
    # Live retrieval first (more specific), then static fallback notes
    doctrine = (live_doctrine + static_doctrine)[:4]

    static_strategic = _strategic_notes(actor, infra_label, tension_level)
    live_strategic = _retrieval_csis_notes(actor, infra_label)
    strategic = (live_strategic + static_strategic)[:3]
    summary = _scenario_summary(actor, infra_label, tension_level, events or [], query)

    return {
        "id": sid,
        "name": f"Operation {_codename(query)}",
        "brief": (
            f"{actor} has been observed conducting cyber operations targeting {infra_label}. "
            f"Scenario trigger: {query}. "
            f"{tension_desc}"
            f"Threat intelligence derived from fused OSINT (GDELT, LiveUAMap, UCDP, GTD). {brief_suffix} "
            "Blue Team must assess the threat and develop a defensive response."
        ),
        "blue_objectives": [
            f"Assess and contain threat to {infra_label}",
            f"Stabilize operations impacted by scenario condition: {query[:120]}",
            "Identify adversary TTPs and initial access vector",
            "Evict actor while maintaining operational continuity",
            "Preserve evidence for attribution and coordination",
        ],
        "red_posture": (
            f"{actor} conducting reconnaissance and pre-positioning against {infra_label}. "
            f"Threat derived from fused OSINT (GDELT/LiveUAMap/UCDP/GTD) — exact foothold unknown. "
            f"Tension level: {tension_level:.2f}. Assume persistence capability. "
            f"Assessed posture: {red_posture_label}. "
            "Escalation authority: disruption of primary operations."
        ),
        "assets": assets,
        "tension_level": round(tension_level, 3),
        "actor_relationships": actor_relationships or [],
        "recent_events": recent_events_dicts,
        "sources_used": [],  # filled by seeder

        # Fused intelligence fields
        "tension_score": t_score,
        "conflict_score": c_score,
        "infrastructure_risk_score": i_score,
        "adversary_aggression_score": agg_score,
        "scenario_summary": summary,
        "doctrine_notes": doctrine,
        "strategic_notes": strategic,
        "infrastructure": infrastructure or [],
        "recommended_red_posture": red_posture_label,
    }
