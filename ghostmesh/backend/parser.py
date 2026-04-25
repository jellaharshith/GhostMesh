"""
Deterministic keyword-based parser: plain-English Blue move → structured ParsedMove.
Never hallucinates — uses "unknown" for fields that cannot be inferred.
"""
from __future__ import annotations
import re
from typing import Any, Dict, List, Tuple


# ── Action verb taxonomy ─────────────────────────────────────────────────────

ACTION_MAP: List[Tuple[List[str], str, str, str, str]] = [
    # keywords          action          technique_family        stealth  risk
    (["isolate", "segment", "quarantine"],
     "isolate",         "network-segmentation",                 "high",  "low"),
    (["patch", "remediat", "update", "fix vuln"],
     "patch",           "vulnerability-management",             "high",  "low"),
    (["hunt", "threat hunt", "search for", "look for"],
     "hunt",            "threat-hunting",                       "high",  "medium"),
    (["deceiv", "honeypot", "lure", "decoy", "canary"],
     "deceive",         "deception-technology",                 "high",  "low"),
    (["monitor", "watch", "observe", "log"],
     "monitor",         "detection-and-monitoring",             "high",  "low"),
    (["block", "deny", "firewall", "acl", "rule"],
     "block",           "access-control",                       "high",  "low"),
    (["deploy", "install", "stand up", "spin up"],
     "deploy",          "capability-deployment",                "medium","medium"),
    (["restore", "recover", "reimage", "rebuild", "wipe"],
     "restore",         "incident-recovery",                    "high",  "medium"),
    (["scan", "enumerate", "nmap", "probe"],
     "scan",            "active-reconnaissance",                "low",   "medium"),
    (["credential", "password", "reset cred", "rotate"],
     "rotate-credentials", "credential-management",            "high",  "low"),
    (["evacuate", "shutdown", "power off", "offline"],
     "evacuate",        "emergency-shutdown",                   "high",  "high"),
]

STEALTH_KEYWORDS = {
    "quiet": "high",
    "covert": "high",
    "silent": "high",
    "stealthily": "high",
    "noisy": "low",
    "aggressive": "low",
    "loud": "low",
}

RISK_KEYWORDS = {
    "carefully": "low",
    "slowly": "low",
    "risky": "high",
    "dangerous": "high",
    "urgent": "high",
    "immediately": "high",
    "asap": "high",
}

# Asset name tokens for target extraction
KNOWN_TARGETS = [
    "hmi", "hmi-01", "historian", "his-01", "jump host", "jh-01",
    "eng-ws", "firewall", "fw-ot", "vpn", "vpn-gw",
    "scada", "ot network", "corporate vlan", "dmz", "engineering workstation",
]

KNOWN_INTENTS = {
    "isolate":            "contain threat / limit lateral movement",
    "patch":              "close known vulnerability / remove initial access vector",
    "hunt":               "find adversary persistence / map compromise extent",
    "deceive":            "misdirect adversary / slow down attacker",
    "monitor":            "increase visibility / detect adversary activity",
    "block":              "prevent adversary access / enforce perimeter",
    "deploy":             "expand defensive capability",
    "restore":            "recover system integrity / evict persistence",
    "scan":               "map environment / identify exposure",
    "rotate-credentials": "invalidate stolen credentials",
    "evacuate":           "prevent ICS impact / protect physical systems",
}


def _find_action(text: str) -> Tuple[str, str, str, str]:
    lower = text.lower()
    for keywords, action, technique, stealth, risk in ACTION_MAP:
        if any(kw in lower for kw in keywords):
            return action, technique, stealth, risk
    return "unknown", "unknown", "medium", "medium"


def _find_target(text: str) -> str:
    lower = text.lower()
    for t in KNOWN_TARGETS:
        if t in lower:
            return t.upper().replace(" ", "-")
    return "unknown"


def _find_stealth(text: str, default: str) -> str:
    lower = text.lower()
    for kw, level in STEALTH_KEYWORDS.items():
        if kw in lower:
            return level
    return default


def _find_risk(text: str, default: str) -> str:
    lower = text.lower()
    for kw, level in RISK_KEYWORDS.items():
        if kw in lower:
            return level
    return default


def _find_time_horizon(text: str) -> str:
    lower = text.lower()
    if any(w in lower for w in ["immediately", "now", "asap", "urgent", "right now"]):
        return "immediate (< 1 hour)"
    if any(w in lower for w in ["tonight", "today", "next few hours"]):
        return "short (< 8 hours)"
    if any(w in lower for w in ["tomorrow", "next day", "overnight"]):
        return "medium (24 hours)"
    return "unspecified"


def _build_assumptions(action: str, target: str, text: str) -> List[str]:
    assumptions: List[str] = []
    if target == "unknown":
        assumptions.append("Target system not explicitly named — inferred from context")
    if action == "unknown":
        assumptions.append("Action verb not recognized — move classified as unknown")
    if "without" not in text.lower() and action in ("isolate", "evacuate"):
        assumptions.append("Assumes change-window approval is in place")
    if action in ("hunt", "scan"):
        assumptions.append("Assumes EDR/logging agents are deployed on target systems")
    if action == "patch":
        assumptions.append("Assumes patch is tested and available in internal repo")
    return assumptions or ["No critical assumptions identified"]


def _confidence(action: str, target: str, assumptions: List[str]) -> float:
    score = 1.0
    if action == "unknown":
        score -= 0.4
    if target == "unknown":
        score -= 0.2
    score -= 0.05 * max(0, len(assumptions) - 1)
    return round(max(0.1, score), 2)


def parse_move(text: str) -> Dict[str, Any]:
    action, technique, default_stealth, default_risk = _find_action(text)
    target = _find_target(text)
    stealth = _find_stealth(text, default_stealth)
    risk = _find_risk(text, default_risk)
    time_horizon = _find_time_horizon(text)
    intent = KNOWN_INTENTS.get(action, "unknown — review manually")
    assumptions = _build_assumptions(action, target, text)
    confidence = _confidence(action, target, assumptions)

    return {
        "actor": "Blue Team",
        "action": action,
        "target": target,
        "intent": intent,
        "technique_family": technique,
        "stealth_level": stealth,
        "risk": risk,
        "time_horizon": time_horizon,
        "assumptions": assumptions,
        "confidence": confidence,
    }
