"""
Probabilistic adjudicator: parsed move + scenario → outcome.
Uses seeded RNG for reproducible-per-turn variance — no binary outcomes.
"""
from __future__ import annotations
import random
from typing import Any, Dict, List, Tuple


# ── Base rates by action ─────────────────────────────────────────────────────
# (success_base, detection_base, attribution_base)
ACTION_BASE_RATES: Dict[str, Tuple[float, float, float]] = {
    "isolate":            (0.85, 0.30, 0.10),
    "patch":              (0.90, 0.20, 0.05),
    "hunt":               (0.65, 0.20, 0.05),
    "deceive":            (0.70, 0.10, 0.05),
    "monitor":            (0.95, 0.10, 0.03),
    "block":              (0.80, 0.25, 0.08),
    "deploy":             (0.75, 0.30, 0.10),
    "restore":            (0.80, 0.40, 0.15),
    "scan":               (0.70, 0.50, 0.20),
    "rotate-credentials": (0.92, 0.15, 0.05),
    "evacuate":           (0.70, 0.60, 0.25),
    "unknown":            (0.40, 0.30, 0.10),
}

STEALTH_MODIFIER = {"high": 1.0, "medium": 0.85, "low": 0.65}
RISK_MODIFIER    = {"low": 1.05, "medium": 1.0,  "high": 0.90}

# Effects library: action → (success_effects, partial_effects)
EFFECTS_LIBRARY: Dict[str, Tuple[List[str], List[str]]] = {
    "isolate": (
        ["Target system fully segmented from OT network",
         "Adversary C2 channel severed",
         "Lateral movement to HMI-01 blocked"],
        ["Segmentation partial — historian still reachable via VLAN 42",
         "Adversary may retain local persistence on jump host"],
    ),
    "patch": (
        ["CVE-2023-46805 remediated on VPN-GW",
         "Initial access vector closed",
         "Adversary lateral movement tooling blocked at perimeter"],
        ["Patch applied to VPN-GW only — downstream appliances still unpatched",
         "Scheduled task persistence on JH-01 unaffected by patch"],
    ),
    "hunt": (
        ["Adversary scheduled task on JH-01 discovered and documented",
         "Historian exfil staging directory identified",
         "Full kill-chain mapped for attribution"],
        ["Hunt identified foothold on JH-01 but historian access not fully scoped",
         "Lateral movement artifacts found — staging on HMI-01 unconfirmed"],
    ),
    "deceive": (
        ["Honeypot drew adversary away from HMI-01",
         "Adversary interaction with decoy logged — TTPs captured",
         "HMI-01 exposure window reduced by 60%"],
        ["Honeypot partially engaged — adversary moved to decoy but retained HIS-01 access",
         "Deception artifact planted; adversary has not yet interacted"],
    ),
    "monitor": (
        ["Enhanced logging active on all OT segments",
         "Adversary beaconing pattern detected — C2 interval identified",
         "Real-time alerting enabled for HMI-01 and HIS-01"],
        ["Monitoring deployed on IT segment; OT visibility still limited",
         "Log ingestion lag of ~5 min — near-real-time, not real-time"],
    ),
    "block": (
        ["Adversary egress IP blocked at FW-OT",
         "Inbound VPN access from adversary subnet denied",
         "Exfil channel disrupted"],
        ["Block applied at perimeter — adversary may pivot through compromised internal host",
         "IP block effective; domain-fronting C2 variant not covered"],
    ),
    "deploy": (
        ["EDR deployed to JH-01 and HIS-01",
         "Deception grid live across OT VLAN",
         "Capability operational — adversary activity now visible"],
        ["EDR deployed to JH-01; historian deployment queued for next maintenance window",
         "Capability staged but not fully tuned — high false-positive rate expected"],
    ),
    "restore": (
        ["JH-01 reimaged — persistence removed",
         "HIS-01 restored from known-good snapshot",
         "Adversary evicted from both compromised hosts"],
        ["JH-01 reimaged successfully; HIS-01 snapshot pre-dates latest config — data gap",
         "System restored but root cause (VPN vuln) not yet remediated"],
    ),
    "scan": (
        ["Full OT network map generated",
         "3 additional unmanaged devices discovered on VLAN 10",
         "Adversary staging directory fingerprinted"],
        ["Scan completed on IT segment; OT scan paused to avoid ICS disruption",
         "Partial asset inventory — historians and HMIs not fully enumerated"],
    ),
    "rotate-credentials": (
        ["All service account credentials rotated",
         "Adversary stolen credentials invalidated",
         "MFA enforced on VPN-GW and jump host"],
        ["Domain credentials rotated; local admin accounts on HIS-01 not yet updated",
         "Credential rotation complete — session tokens may still be valid for up to 1 hour"],
    ),
    "evacuate": (
        ["HMI-01 safely taken offline — grid control shifted to backup RTUs",
         "Physical safety maintained — no load-shedding event",
         "Adversary denied Stage 7 access window"],
        ["HMI-01 offline — partial manual control mode active",
         "Backup RTU coverage incomplete for substations 3 and 7"],
    ),
    "unknown": (
        ["Move executed — outcome uncertain",
         "Recommend clarifying intent and resubmitting"],
        ["Move partially executed — effect scope unclear"],
    ),
}

CASCADE_LIBRARY: Dict[str, List[str]] = {
    "isolate":  ["Adversary may detect isolation and accelerate timeline",
                 "Dependent IT services may experience brief disruption"],
    "patch":    ["Patch deployment requires 15-min maintenance window — coordinate with ops"],
    "hunt":     ["Hunt findings may trigger incident escalation to CISA"],
    "deceive":  ["Deception success may give false confidence — continue active monitoring"],
    "monitor":  ["Increased log volume may stress SIEM capacity"],
    "block":    ["Block may accelerate adversary pivot to alternative C2 channel"],
    "deploy":   ["EDR agent install may cause brief performance hit on OT historians"],
    "restore":  ["Restoration reveals pre-compromise state — adversary may reinfect if vuln open"],
    "scan":     ["Active scan may generate noise detectable by adversary"],
    "rotate-credentials": ["Rotation will lock out any Blue Team members using shared credentials"],
    "evacuate": ["Offline HMI triggers automatic alarm in control room — prepare staff"],
    "unknown":  [],
}


def adjudicate(parsed: Dict[str, Any], scenario: Dict[str, Any], turn_id: int) -> Dict[str, Any]:
    action = parsed.get("action", "unknown")
    stealth = parsed.get("stealth_level", "medium")
    risk = parsed.get("risk", "medium")
    confidence = parsed.get("confidence", 0.5)

    base_success, base_detect, base_attrib = ACTION_BASE_RATES.get(
        action, ACTION_BASE_RATES["unknown"]
    )

    rng = random.Random(turn_id * 31337 + hash(action) % 9999)

    s_mod = STEALTH_MODIFIER.get(stealth, 1.0)
    r_mod = RISK_MODIFIER.get(risk, 1.0)

    jitter = rng.uniform(-0.08, 0.08)
    success_prob = round(min(0.98, max(0.05, base_success * s_mod * r_mod * confidence + jitter)), 2)
    detection_risk = round(min(0.99, max(0.02, base_detect * (2.0 - s_mod) + rng.uniform(-0.05, 0.05))), 2)
    attribution_risk = round(min(0.99, max(0.01, base_attrib * (1 + detection_risk) + rng.uniform(-0.03, 0.03))), 2)

    success_effects, partial_effects = EFFECTS_LIBRARY.get(action, EFFECTS_LIBRARY["unknown"])
    cascade = CASCADE_LIBRARY.get(action, [])

    if success_prob >= 0.75:
        effects = success_effects
        outcome_word = "high confidence"
    elif success_prob >= 0.50:
        effects = partial_effects + [success_effects[0]] if success_effects else partial_effects
        outcome_word = "partial success likely"
    else:
        effects = partial_effects
        outcome_word = "uncertain — partial effect only"

    cascading = cascade[:2] if cascade else ["No significant cascading effects identified"]

    rationale = (
        f"Action '{action}' against '{parsed.get('target', 'unknown')}' assessed as {outcome_word}. "
        f"Stealth posture '{stealth}' yields detection risk {detection_risk:.0%}. "
        f"Confidence driven by parser score {confidence:.0%}."
    )

    return {
        "success_probability": success_prob,
        "detection_risk": detection_risk,
        "attribution_risk": attribution_risk,
        "effects": effects,
        "cascading_effects": cascading,
        "rationale": rationale,
    }
