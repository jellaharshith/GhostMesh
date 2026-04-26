"""
Red Cell: adaptive adversary response engine.

State machine tracks adversary pressure, remaining footholds, and objective
urgency across turns. Posture model drives tier selection. Doctrine-grounded
playbook prevents repeat responses. Deterministic core — no LLM in hot path.
"""
from __future__ import annotations
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple


# ── Cached public-source APT doctrine ─────────────────────────────────────────
# MITRE ATT&CK for ICS: Stage-6 → Stage-7 transition TTPs
# Keyed (blue_action, posture) → (doctrine_hint, preferred_target_override | None)

APT_X_DOCTRINE: Dict[Tuple[str, str], Tuple[str, Optional[str]]] = {
    # T0817 Drive-by / T0843 Program Download — prefer ENG-WS-1 as relay to HMI
    ("isolate",   "aggressive"):    ("APT-X Stage-6: pivot to HMI-01 via ENG-WS-1 before segmentation hardens",
                                     "HMI-01 via ENG-WS-1 relay"),
    ("isolate",   "opportunistic"): ("APT-X doctrine: maintain alternate C2 via pre-staged email relay",
                                     "HIS-01 outbound SMTP relay"),
    # T0859 Valid Accounts — vendor VPN secondary access
    ("patch",     "aggressive"):    ("APT-X Stage-6: vendor VPN credentials pre-identified for secondary entry",
                                     "FW-OT vendor management port"),
    ("patch",     "opportunistic"): ("APT-X doctrine: fall back to existing host persistence post-patch",
                                     "JH-01 scheduled task"),
    # T0853 Scripting / LOLBins — blend with admin noise under monitoring
    ("monitor",   "aggressive"):    ("APT-X doctrine: switch to LOLBins (WMI, certutil) to blend with admin traffic",
                                     "JH-01 and HIS-01"),
    ("monitor",   "opportunistic"): ("APT-X doctrine: reduce C2 beacon cadence to sub-threshold interval",
                                     "JH-01 C2 channel"),
    # Counter-hunt: fileless pivot + false-flag artifacts
    ("hunt",      "conservative"):  ("APT-X doctrine: burn disk artifacts, transition to fileless implant",
                                     "JH-01 disk artifacts"),
    ("hunt",      "opportunistic"): ("APT-X doctrine: seed false IOCs for attribution misdirection",
                                     "JH-01 and HIS-01 event logs"),
    # Credential theft recovery — keylogger capture new creds
    ("rotate-credentials", "aggressive"):    ("APT-X Stage-6: keylogger on JH-01 captures new creds post-rotation",
                                              "JH-01 admin session"),
    ("rotate-credentials", "opportunistic"): ("APT-X doctrine: session token replay within 1-hour validity window",
                                              "Active VPN session token"),
    # Exploit divided attention during deception
    ("deceive",   "aggressive"):    ("APT-X doctrine: use decoy as cover for simultaneous real-asset access",
                                     "HMI-01 while Blue watches honeypot"),
    # ICS impact window during HMI evacuation
    ("evacuate",  "desperate"):     ("APT-X Stage-7: target backup RTU infrastructure during HMI offline gap",
                                     "Backup RTU VLAN"),
    ("evacuate",  "aggressive"):    ("APT-X doctrine: HMI offline = manual-ops gap; exploit reduced control visibility",
                                     "Backup RTU VLAN"),
    # Domain-fronting under blocking
    ("block",     "aggressive"):    ("APT-X doctrine: domain-fronted HTTPS C2 via CDN, bypasses IP rules",
                                     "CDN-masked C2 endpoint"),
    ("block",     "opportunistic"): ("APT-X doctrine: pivot C2 to cloud sync (OneDrive) — trusted service bypass",
                                     "ENG-WS-1 OneDrive client"),
    # Pre-stage destructive payload under active restore/deploy pressure
    ("restore",   "desperate"):     ("APT-X Stage-6: data integrity attack on historian before eviction completes",
                                     "HIS-01 historian database"),
    ("deploy",    "desperate"):     ("APT-X Stage-6: deploy destructive payload trigger ahead of EDR coverage",
                                     "HIS-01 historian data store"),
}


# ── Response playbook ──────────────────────────────────────────────────────────
# Each cell: list of variant dicts (primary first, alternate second).
# Variant rotation used for repeat-suppression.

RESPONSE_PLAYBOOK: Dict[str, Dict[str, List[Dict[str, str]]]] = {
    "isolate": {
        "retreat": [
            {"red_action": "Suspend C2 beaconing and maintain dormant persistence",
             "target": "JH-01 scheduled task",
             "intent": "Avoid detection by reducing network noise during isolation event"},
            {"red_action": "Reduce implant polling to once per 8 hours and disable file-based artifacts",
             "target": "JH-01 fileless implant",
             "intent": "Stay below monitoring thresholds while isolation hardens"},
        ],
        "hold": [
            {"red_action": "Pivot C2 to out-of-band channel via compromised email account",
             "target": "HIS-01 outbound SMTP relay",
             "intent": "Maintain persistence through alternate C2 while primary channel is disrupted"},
            {"red_action": "Re-route C2 through DNS-over-HTTPS to blend with legitimate resolver traffic",
             "target": "HIS-01 → external DoH resolver",
             "intent": "Bypass isolation by masking C2 in encrypted DNS traffic"},
        ],
        "escalate": [
            {"red_action": "Accelerate lateral movement toward HMI-01 before segmentation hardens",
             "target": "HMI-01 via ENG-WS-1 relay",
             "intent": "Achieve Stage 7 foothold before Blue completes network hardening"},
            {"red_action": "Stage tooling on ENG-WS-1 engineering workstation for HMI access",
             "target": "ENG-WS-1",
             "intent": "Pre-position on uncovered asset before isolation sweep reaches it"},
        ],
    },
    "patch": {
        "retreat": [
            {"red_action": "Shift reliance from VPN exploit to existing persistence on JH-01",
             "target": "JH-01 scheduled task",
             "intent": "Re-entry vector closed — depend on existing foothold until new vector found"},
            {"red_action": "Suspend offensive activity and audit remaining access paths",
             "target": "All current C2 channels",
             "intent": "Pause to understand patch scope before committing to alternate approach"},
        ],
        "hold": [
            {"red_action": "Stage secondary access via supply-chain vendor VPN credentials",
             "target": "FW-OT vendor management port",
             "intent": "Establish backup entry vector through third-party access"},
            {"red_action": "Enumerate unpatched downstream appliances for secondary persistence vector",
             "target": "ENG-WS-1 and HIS-01 patch status",
             "intent": "Identify which assets remain exploitable after primary patch deployment"},
        ],
        "escalate": [
            {"red_action": "Deploy wiper pre-stage on HIS-01 as leverage before patch hardens position",
             "target": "HIS-01 historian data store",
             "intent": "Establish destructive deterrent to complicate Blue remediation decision"},
            {"red_action": "Exfiltrate historian engineering config before patch window closes access",
             "target": "HIS-01 config export",
             "intent": "Collect maximum ICS intelligence before access vector closes"},
        ],
    },
    "hunt": {
        "retreat": [
            {"red_action": "Wipe artifacts from JH-01 and rotate implant to fileless variant",
             "target": "JH-01 disk artifacts",
             "intent": "Deny forensic evidence and reset detection baseline"},
            {"red_action": "Migrate implant to memory-only execution and disable scheduled task",
             "target": "JH-01 persistence mechanism",
             "intent": "Eliminate huntable artifacts while preserving access capability"},
        ],
        "hold": [
            {"red_action": "Plant false flag artifacts pointing to unrelated nation-state group",
             "target": "JH-01 and HIS-01 event logs",
             "intent": "Confuse attribution and buy operational time"},
            {"red_action": "Introduce synthetic IOCs matching known commodity malware signatures",
             "target": "HIS-01 filesystem artifacts",
             "intent": "Flood Blue analyst pipeline with misleading threat indicators"},
        ],
        "escalate": [
            {"red_action": "Accelerate exfiltration of historian configuration data before eviction",
             "target": "HIS-01 config export",
             "intent": "Collect maximum intelligence before foothold is lost"},
            {"red_action": "Push pre-staged HMI payload while Blue analysts focused on JH-01 hunt",
             "target": "HMI-01 via ENG-WS-1",
             "intent": "Exploit Blue attention on hunt to advance kill-chain on primary target"},
        ],
    },
    "deceive": {
        "retreat": [
            {"red_action": "Avoid honeypot — restrict activity to known-good target paths",
             "target": "HMI-01 direct",
             "intent": "Operate only on confirmed real assets to avoid deception infrastructure"},
            {"red_action": "Suspend lateral movement and observe Blue deception deployment pattern",
             "target": "All OT network activity",
             "intent": "Map deception coverage before committing to next move"},
        ],
        "hold": [
            {"red_action": "Interact minimally with decoy to probe Blue deception strategy",
             "target": "Honeypot node",
             "intent": "Map Blue deception coverage while limiting exposure"},
            {"red_action": "Test decoy response timing to fingerprint Blue monitoring architecture",
             "target": "Honeypot node — timing probe",
             "intent": "Determine alert thresholds before committing to real-asset access"},
        ],
        "escalate": [
            {"red_action": "Use deception infrastructure as distraction — simultaneous move on HMI-01",
             "target": "HMI-01 while Blue watches honeypot",
             "intent": "Split Blue attention between decoy and real objective"},
            {"red_action": "Trigger honeypot alerts deliberately to saturate Blue SOC while exfiltrating historian data",
             "target": "HIS-01 while Blue responds to honeypot alert",
             "intent": "Use deception noise as operational cover for primary objective"},
        ],
    },
    "monitor": {
        "retreat": [
            {"red_action": "Drop beacon frequency to once per 6 hours to evade threshold alerts",
             "target": "JH-01 C2 channel",
             "intent": "Stay below monitoring alert thresholds"},
            {"red_action": "Disable implant auto-run and switch to operator-triggered callbacks only",
             "target": "JH-01 and HIS-01 implants",
             "intent": "Eliminate predictable beaconing patterns that feed statistical detection"},
        ],
        "hold": [
            {"red_action": "Shift to living-off-the-land techniques using native Windows tools",
             "target": "JH-01 and HIS-01",
             "intent": "Blend with legitimate admin activity to evade enhanced monitoring"},
            {"red_action": "Tunnel C2 through legitimate scheduled task using certutil and WMI",
             "target": "JH-01 admin task scheduler",
             "intent": "Disguise C2 traffic as normal administrative operations"},
        ],
        "escalate": [
            {"red_action": "Exfiltrate historian data via encrypted DNS tunnel before monitoring matures",
             "target": "HIS-01 → external DNS resolver",
             "intent": "Complete primary intelligence objective before detection capability fully operational"},
            {"red_action": "Push HMI-01 access attempt during monitoring deployment gap on OT segment",
             "target": "HMI-01 (OT segment not yet covered)",
             "intent": "Exploit coverage gap before SIEM ingestion reaches OT VLAN"},
        ],
    },
    "block": {
        "retreat": [
            {"red_action": "Suspend operations and await intelligence on Blue firewall ruleset",
             "target": "All current C2 channels",
             "intent": "Understand scope of Blue blocking before committing to alternate path"},
            {"red_action": "Go dark for 12 hours and probe block effectiveness via passive timing checks",
             "target": "JH-01 passive beacon",
             "intent": "Determine block scope without burning active C2 infrastructure"},
        ],
        "hold": [
            {"red_action": "Pivot C2 to domain-fronted HTTPS through CDN infrastructure",
             "target": "CDN-masked C2 endpoint",
             "intent": "Bypass IP-based blocking via domain fronting"},
            {"red_action": "Switch to ICMP-tunneled C2 to bypass layer-4 block rules",
             "target": "JH-01 ICMP tunnel",
             "intent": "Use protocol not covered by firewall ACL to restore C2 channel"},
        ],
        "escalate": [
            {"red_action": "Establish persistence via legitimate cloud sync service (OneDrive) for C2",
             "target": "ENG-WS-1 OneDrive client",
             "intent": "Use trusted cloud service to bypass perimeter blocks"},
            {"red_action": "Route C2 through Microsoft Teams webhook to appear as legitimate SaaS traffic",
             "target": "ENG-WS-1 Teams client",
             "intent": "Abuse business-critical SaaS channel that Blue cannot block without operational impact"},
        ],
    },
    "deploy": {
        "retreat": [
            {"red_action": "Disable implant on newly-covered hosts and shift to uncovered assets",
             "target": "ENG-WS-1 (no EDR coverage detected)",
             "intent": "Move laterally away from newly instrumented hosts"},
            {"red_action": "Suspend activity on EDR-covered hosts and audit remaining coverage gaps",
             "target": "All active implants",
             "intent": "Preserve operational capability by identifying unmonitored attack surface"},
        ],
        "hold": [
            {"red_action": "Tamper with EDR configuration to reduce telemetry fidelity",
             "target": "JH-01 EDR agent config",
             "intent": "Degrade Blue visibility while maintaining presence"},
            {"red_action": "Add exclusions to EDR agent for implant working directory",
             "target": "HIS-01 EDR configuration",
             "intent": "Blind EDR to active persistence path without disabling entire agent"},
        ],
        "escalate": [
            {"red_action": "Deploy destructive payload trigger on HIS-01 ahead of eviction",
             "target": "HIS-01 historian data store",
             "intent": "Establish leverage — threaten data destruction to deter Blue eviction"},
            {"red_action": "Stage ransomware pre-position on HIS-01 and HMI-01 as dual-leverage threat",
             "target": "HIS-01 and HMI-01 data stores",
             "intent": "Escalate destructive threat scope to complicate Blue decision calculus"},
        ],
    },
    "restore": {
        "retreat": [
            {"red_action": "Accept loss of current foothold — await opportunity to reinfect via VPN",
             "target": "VPN-GW (if unpatched)",
             "intent": "Preserve capability by not burning unpatched vector in response"},
            {"red_action": "Stand down and await Blue maintenance window for reinfection opportunity",
             "target": "VPN-GW post-maintenance",
             "intent": "Conserve tooling — reinfection more viable than burning backup access path"},
        ],
        "hold": [
            {"red_action": "Reinfect restored system via same vector within maintenance window",
             "target": "JH-01 post-reimage",
             "intent": "Re-establish persistence before vulnerability is patched"},
            {"red_action": "Establish foothold on ENG-WS-1 as redundant persistence while JH-01 is restored",
             "target": "ENG-WS-1",
             "intent": "Maintain operational continuity through secondary host while primary is reimaged"},
        ],
        "escalate": [
            {"red_action": "Execute Stage 6 payload — disrupt historian data integrity before eviction completes",
             "target": "HIS-01 historian database",
             "intent": "Inflict maximum impact before Blue fully evicts presence"},
            {"red_action": "Trigger pre-staged HMI payload to force operational crisis during Blue restoration activity",
             "target": "HMI-01 control interface",
             "intent": "Create simultaneous crisis that forces Blue to choose between eviction and operations"},
        ],
    },
    "scan": {
        "retreat": [
            {"red_action": "Detect scan traffic and go silent for 24 hours",
             "target": "All active implants",
             "intent": "Avoid being fingerprinted during active Blue scan"},
            {"red_action": "Reduce all implant network activity to zero during active scan window",
             "target": "JH-01 and HIS-01 implants",
             "intent": "Present zero anomalous traffic during Blue enumeration phase"},
        ],
        "hold": [
            {"red_action": "Feed false open ports to confuse Blue asset inventory",
             "target": "JH-01 network interface",
             "intent": "Corrupt Blue's network map with honeyed port responses"},
            {"red_action": "Spoof additional hosts to inflate Blue asset inventory and waste analyst time",
             "target": "VLAN 10 broadcast domain",
             "intent": "Force Blue to process phantom assets, delaying accurate network mapping"},
        ],
        "escalate": [
            {"red_action": "Use Blue scan timing as cover noise to exfiltrate historian config",
             "target": "HIS-01",
             "intent": "Blend exfil traffic with Blue-generated scan traffic"},
            {"red_action": "Execute lateral movement to ENG-WS-1 while scan traffic provides network cover",
             "target": "ENG-WS-1 via lateral move",
             "intent": "Move to new host under cover of elevated network noise from Blue scan"},
        ],
    },
    "rotate-credentials": {
        "retreat": [
            {"red_action": "Accept credential loss — rely on API key cached in historian service account",
             "target": "HIS-01 service account",
             "intent": "Survive credential rotation via pre-cached non-rotating credential"},
            {"red_action": "Fall back to certificate-based authentication pre-staged on JH-01",
             "target": "JH-01 certificate store",
             "intent": "Use non-password auth mechanism unaffected by credential rotation"},
        ],
        "hold": [
            {"red_action": "Capture new credentials during post-rotation authentication with keylogger",
             "target": "JH-01 admin session",
             "intent": "Re-acquire credentials via keylogger already installed on jump host"},
            {"red_action": "Monitor post-rotation admin activity to harvest re-used password patterns",
             "target": "HIS-01 authentication log",
             "intent": "Identify credential reuse across systems during rotation confusion window"},
        ],
        "escalate": [
            {"red_action": "Use token replay against active admin session before rotation completes",
             "target": "Active VPN session token",
             "intent": "Exploit session token validity window post-credential rotation"},
            {"red_action": "Abuse Kerberos ticket cache on JH-01 before TGT expiry post-rotation",
             "target": "JH-01 Kerberos TGT cache",
             "intent": "Use cached Kerberos tickets valid for up to 10 hours regardless of password change"},
        ],
    },
    "evacuate": {
        "retreat": [
            {"red_action": "Stand down — objective window closed, preserve remaining infrastructure",
             "target": "All current footholds",
             "intent": "Avoid operational exposure when primary target offline"},
            {"red_action": "Suspend all OT-facing operations and maintain IT persistence only",
             "target": "JH-01 and HIS-01 (IT side)",
             "intent": "Preserve capability for re-engagement when HMI-01 comes back online"},
        ],
        "hold": [
            {"red_action": "Maintain persistence on HIS-01 and await HMI-01 restoration",
             "target": "HIS-01",
             "intent": "Wait for HMI to come back online before proceeding with ICS impact"},
            {"red_action": "Establish deeper foothold on ENG-WS-1 for HMI access during restoration",
             "target": "ENG-WS-1",
             "intent": "Pre-position on engineering workstation for HMI re-access post-restoration"},
        ],
        "escalate": [
            {"red_action": "Target backup RTU infrastructure during gap created by HMI evacuation",
             "target": "Backup RTU VLAN",
             "intent": "Exploit control gap during manual operations mode"},
            {"red_action": "Attack substation protection relay during manual operations window",
             "target": "Backup RTU relay configuration",
             "intent": "Use reduced operator visibility during manual mode to create physical safety impact"},
        ],
    },
    "unknown": {
        "retreat": [
            {"red_action": "Monitor Blue activity pattern before committing to response",
             "target": "Blue Team network activity",
             "intent": "Gather intelligence on Blue intent before acting"},
            {"red_action": "Suspend outbound operations and conduct passive observation only",
             "target": "All active implants",
             "intent": "Reduce exposure while Blue intent remains unclear"},
        ],
        "hold": [
            {"red_action": "Continue current operation unchanged",
             "target": "Existing footholds",
             "intent": "Maintain steady-state until Blue intent is clearer"},
            {"red_action": "Conduct minimal-footprint reconnaissance on Blue activity indicators",
             "target": "JH-01 passive sensor",
             "intent": "Gather information on Blue posture without committing to offensive action"},
        ],
        "escalate": [
            {"red_action": "Accelerate exfiltration while Blue posture is unclear",
             "target": "HIS-01",
             "intent": "Exploit Blue confusion to advance primary objective"},
            {"red_action": "Push HMI-01 staging while Blue is preoccupied with unknown operation",
             "target": "HMI-01 via ENG-WS-1",
             "intent": "Advance kill-chain during Blue attention gap"},
        ],
    },
}


# ── Pressure class weights ─────────────────────────────────────────────────────
_PRESSURE_WEIGHT: Dict[str, float] = {
    "restore":            1.00,
    "rotate-credentials": 1.00,
    "isolate":            0.70,
    "block":              0.70,
    "patch":              0.70,
    "hunt":               0.40,
    "monitor":            0.40,
    "deploy":             0.40,
    "scan":               0.40,
    "deceive":            0.30,
    "evacuate":           0.50,
    "unknown":            0.20,
}

# Outcome class multipliers
_OUTCOME_FACTOR: Dict[str, float] = {
    "full":              1.00,
    "partial-strong":    0.65,
    "partial-weak":      0.30,
    "failure":           0.00,
}

# Footholds that start in play
_INITIAL_FOOTHOLDS: Set[str] = {
    "jh01_scheduled_task",
    "his01_read",
    "vpn_reentry",
    "hmi01_staging",
}

# Foothold reference strings used in response text — for gate checks
_FOOTHOLD_TOKENS: Dict[str, List[str]] = {
    "jh01_scheduled_task": ["jh-01", "jh01", "jump host"],
    "his01_read":          ["his-01", "his01", "historian"],
    "vpn_reentry":         ["vpn", "vpn-gw"],
    "hmi01_staging":       ["hmi-01", "hmi01", "hmi"],
}


# ── Red state dataclass ────────────────────────────────────────────────────────

@dataclass
class RedState:
    pressure: float = 0.0
    footholds: Set[str] = field(default_factory=lambda: set(_INITIAL_FOOTHOLDS))
    urgency: float = 0.30
    last_red_actions: List[str] = field(default_factory=list)
    last_blue_actions: List[str] = field(default_factory=list)
    turn_count: int = 0


def _outcome_class(effects: List[str]) -> str:
    """Extract outcome class from effects list prefix tag."""
    if not effects:
        return "failure"
    first = effects[0].lower()
    if "[full]" in first:
        return "full"
    if "partial-strong" in first:
        return "partial-strong"
    if "partial-weak" in first:
        return "partial-weak"
    return "failure"


def _compute_red_state(scenario: Dict[str, Any]) -> RedState:
    """Replay turn history to derive current Red state. Gracefully degrades on db error."""
    try:
        from backend.db import list_turns
        history = list_turns()
    except Exception:
        return RedState()

    state = RedState()
    footholds: Set[str] = set(_INITIAL_FOOTHOLDS)
    pressure_accumulator = 0.0
    decay = 0.85

    for i, turn in enumerate(history):
        parsed = turn.get("parsed", {})
        adj = turn.get("adjudication", {})
        red = turn.get("red", {})

        action = parsed.get("action", "unknown")
        success_prob = adj.get("success_probability", 0.0)
        effects = adj.get("effects", [])
        oc = _outcome_class(effects)
        target = parsed.get("target", "").lower()

        weight = _PRESSURE_WEIGHT.get(action, 0.20)
        factor = _OUTCOME_FACTOR.get(oc, 0.0)
        # Recency decay: older turns weigh less
        age_decay = decay ** (len(history) - 1 - i)
        pressure_accumulator += weight * success_prob * factor * age_decay

        # Update footholds from Blue successes
        if oc in ("full", "partial-strong"):
            if action == "restore" and any(t in target for t in ("jh-01", "jh01", "jump")):
                footholds.discard("jh01_scheduled_task")
            if action == "patch" and any(t in target for t in ("vpn", "vpn-gw")):
                footholds.discard("vpn_reentry")
            if action == "isolate":
                footholds.discard("hmi01_staging")
            if action == "rotate-credentials" and oc == "full":
                footholds.discard("vpn_reentry")
        if action == "hunt" and oc == "full":
            # Deterministically drop one foothold based on turn index
            candidates = list(footholds - {"his01_read"})  # preserve read access longer
            if candidates:
                drop_idx = i % len(candidates)
                footholds.discard(candidates[drop_idx])

        # Track last actions
        if red.get("red_action"):
            state.last_red_actions.append(red["red_action"])
        state.last_blue_actions.append(action)

    state.pressure = round(min(2.0, pressure_accumulator), 3)
    state.footholds = footholds
    state.turn_count = len(history)

    # Keep only last 2
    state.last_red_actions = state.last_red_actions[-2:]
    state.last_blue_actions = state.last_blue_actions[-2:]

    # Urgency: base ramps with turns, modulated by HMI access
    urgency = 0.30 + 0.05 * min(state.turn_count, 8)
    hmi_asset = next((a for a in scenario.get("assets", []) if a["name"] == "HMI-01"), None)
    if hmi_asset and hmi_asset.get("status") in ("at-risk", "compromised"):
        urgency += 0.20
    if "hmi01_staging" not in footholds:
        urgency -= 0.15
    # Blue successfully evacuated HMI
    if "evacuate" in state.last_blue_actions and "hmi01_staging" not in footholds:
        urgency -= 0.25
    state.urgency = round(max(0.0, min(1.0, urgency)), 3)

    return state


def _determine_posture(state: RedState) -> str:
    fh = len(state.footholds)
    p = state.pressure
    u = state.urgency

    # Desperate: few footholds + high urgency (last-shot destructive)
    if fh <= 1 and u >= 0.80:
        return "desperate"
    # Conservative: too much pressure or almost no footholds
    if p >= 1.0 or fh <= 1:
        return "conservative"
    # Aggressive: strong position + time pressure
    if fh >= 3 and p < 0.60 and u >= 0.50:
        return "aggressive"
    # Default: opportunistic
    return "opportunistic"


def _determine_tier(posture: str, action: str, success_prob: float,
                    attribution_risk: float) -> str:
    """Deterministic tier selection from posture + situational factors."""
    # Situational override: hunt with high attribution → counter-forensics (retreat)
    if action == "hunt" and attribution_risk >= 0.50:
        return "retreat"

    if posture == "aggressive":
        return "escalate"
    if posture == "conservative":
        return "retreat"
    if posture == "desperate":
        return "escalate"

    # opportunistic
    if action in ("restore", "evacuate", "patch") and success_prob >= 0.75:
        return "escalate"
    return "hold"


def _escalation_level(tier: str, posture: str, action: str, footholds_count: int) -> str:
    if posture == "desperate":
        return "escalate_destructive"
    if (tier == "escalate"
            and action in ("restore", "evacuate", "patch")
            and footholds_count <= 2):
        return "escalate_destructive"
    return tier


def _foothold_lost(response: Dict[str, str], state: RedState) -> bool:
    """Check if a response references a foothold no longer available."""
    text = (response["red_action"] + " " + response["target"]).lower()
    for fh, tokens in _FOOTHOLD_TOKENS.items():
        if fh not in state.footholds:
            if any(tok in text for tok in tokens):
                return True
    return False


def _select_response(action: str, tier: str, state: RedState) -> Tuple[Dict[str, str], int]:
    """
    Pick best non-repeated, foothold-valid response variant.
    Returns (response_dict, variant_index_used).
    """
    playbook = RESPONSE_PLAYBOOK.get(action, RESPONSE_PLAYBOOK["unknown"])

    # Map escalate_destructive → escalate in playbook lookup
    tier_key = tier if tier in playbook else "hold"
    if tier_key not in playbook:
        tier_key = list(playbook.keys())[0]

    variants = playbook[tier_key]

    for idx, variant in enumerate(variants):
        # Skip if repeated
        if variant["red_action"] in state.last_red_actions:
            continue
        # Skip if foothold unavailable
        if _foothold_lost(variant, state):
            continue
        return variant, idx

    # Fallback: try alternate tier (downgrade one notch)
    fallback_order = {"escalate": ["hold", "retreat"], "hold": ["retreat", "escalate"],
                      "retreat": ["hold", "escalate"]}
    for alt_tier in fallback_order.get(tier_key, []):
        if alt_tier in playbook:
            for idx, variant in enumerate(playbook[alt_tier]):
                if not _foothold_lost(variant, state):
                    return variant, idx

    # Last resort: first variant of original tier regardless
    return variants[0], 0


def _apply_doctrine(
    response: Dict[str, str],
    action: str,
    posture: str,
    state: RedState,
) -> Tuple[Dict[str, str], Optional[str]]:
    """Override target/intent from doctrine table if applicable."""
    key = (action, posture)
    if key not in APT_X_DOCTRINE:
        return response, None

    hint, target_override = APT_X_DOCTRINE[key]
    if target_override is None:
        return response, hint

    # Only apply target override if referenced foothold is still active
    target_lower = target_override.lower()
    blocked = False
    for fh, tokens in _FOOTHOLD_TOKENS.items():
        if fh not in state.footholds and any(tok in target_lower for tok in tokens):
            blocked = True
            break

    if blocked:
        return response, None

    updated = dict(response)
    updated["target"] = target_override
    return updated, hint


# ── Optional LLM wording hook ─────────────────────────────────────────────────

def _polish_wording(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    LLM-assisted intent refinement grounded in retrieved JCS/MITRE doctrine.
    Enabled when ANTHROPIC_API_KEY is set (GHOSTMESH_LLM_RED env var ignored).
    Core tier/posture decisions are never delegated here — only the intent
    narrative is enriched.  Falls back silently to deterministic result.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        return response

    try:
        import anthropic  # lazy import
    except ImportError:
        return response

    # Retrieve 2 doctrine snippets to ground the response
    doctrine_ctx = ""
    try:
        from retrieval.service import retrieve
        red_action = response.get("red_action", "")
        rationale = response.get("rationale", "")
        snips = retrieve(f"{red_action} adversary TTP doctrine", k=2, tags=["apt", "mitre", "jcs"])
        if snips:
            doctrine_ctx = "\n".join(f"- {s['text'][:160]}" for s in snips)
    except Exception:
        pass

    system_prompt = (
        "You are the Red Cell operator for APT-X, a sophisticated nation-state adversary. "
        "Your task: write a single concise sentence (≤40 words) that articulates the OPERATIONAL "
        "INTENT behind an adversary action, grounding it in the provided doctrine context. "
        "Output ONLY the intent sentence — no preamble, no markdown, no quotation marks."
    )

    user_msg = (
        f"Action: {response.get('red_action', '')}\n"
        f"Target: {response.get('target', '')}\n"
        f"Current intent: {response.get('intent', '')}\n"
        f"Operational rationale: {response.get('rationale', '')[:300]}\n"
    )
    if doctrine_ctx:
        user_msg += f"\nDoctrine context:\n{doctrine_ctx}"
    user_msg += "\n\nRewrite the intent as a precise, doctrine-grounded operator statement."

    try:
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=120,
            system=system_prompt,
            messages=[{"role": "user", "content": user_msg}],
        )
        refined = msg.content[0].text.strip() if msg.content else ""
        if refined and len(refined) > 10:
            response = dict(response)
            response["intent"] = refined
    except Exception:
        pass  # deterministic result unchanged

    return response


# ── Public entry point ─────────────────────────────────────────────────────────

def generate_red_response(
    parsed: Dict[str, Any],
    adjudication: Dict[str, Any],
    scenario: Dict[str, Any],
    turn_id: int,
) -> Dict[str, Any]:
    action = parsed.get("action", "unknown")
    success_prob = adjudication.get("success_probability", 0.5)
    attribution_risk = adjudication.get("attribution_risk", 0.1)

    # Compute state from full turn history
    state = _compute_red_state(scenario)

    # Posture → tier → response selection
    posture = _determine_posture(state)
    tier = _determine_tier(posture, action, success_prob, attribution_risk)
    response, _variant_idx = _select_response(action, tier, state)

    # Doctrine bias: may override target
    response, doctrine_hint = _apply_doctrine(response, action, posture, state)

    # Escalation level label
    escalation_label = _escalation_level(tier, posture, action, len(state.footholds))

    # Rationale includes state breadcrumbs
    fh_list = ", ".join(sorted(state.footholds)) if state.footholds else "none"
    doctrine_note = f" [{doctrine_hint}]" if doctrine_hint else ""
    # Retrieval-grounded APT TTP citation (best-effort)
    try:
        from retrieval.service import retrieve
        apt_snips = retrieve(f"APT {action} {posture} TTP", k=1, tags=["apt", "mitre"])
        if apt_snips:
            doctrine_note = doctrine_note + f" | {apt_snips[0]['text'][:100]}"
    except Exception:
        pass
    rationale = (
        f"Posture={posture} (pressure {state.pressure:.1f}, "
        f"footholds {len(state.footholds)}: [{fh_list}], "
        f"urgency {state.urgency:.2f}, turn {state.turn_count}). "
        f"Blue '{action}' success={success_prob:.0%}, "
        f"attribution_risk={attribution_risk:.0%}. "
        f"Tier={tier} → {escalation_label}.{doctrine_note}"
    )

    # JCS doctrine-shaped posture note (best-effort, never raises)
    jcs_note = ""
    try:
        from retrieval.service import retrieve as _retrieve
        jcs_snips = _retrieve(
            f"{posture} posture {action} response doctrine",
            k=1,
            tags=["jcs", "doctrine"],
        )
        if jcs_snips:
            jcs_note = f" | JCS: {jcs_snips[0]['text'][:120]}"
    except Exception:
        pass

    # CSIS strategic escalation framing (best-effort, never raises)
    csis_note = ""
    try:
        from retrieval.service import retrieve as _retrieve2
        csis_snips = _retrieve2(
            f"{action} escalation {tier} adversary",
            k=1,
            tags=["csis", "escalation"],
        )
        if csis_snips:
            csis_note = f" | CSIS: {csis_snips[0]['text'][:120]}"
    except Exception:
        pass

    if jcs_note or csis_note:
        rationale = rationale + jcs_note + csis_note

    result = {
        "red_action":       response["red_action"],
        "target":           response["target"],
        "intent":           response["intent"],
        "escalation_level": escalation_label,
        "rationale":        rationale,
    }

    return _polish_wording(result)
