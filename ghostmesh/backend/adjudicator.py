"""
Probabilistic adjudicator: parsed move + scenario → outcome.
Uses seeded RNG for reproducible-per-turn variance — no binary outcomes.

Upgrade: partial success modeling, scenario-aware target fit, conditional
attribution (P(attrib) = P(attrib|detect) * P(detect)), outcome-class-driven
cascades, and composited scoring separated from confidence.
"""
from __future__ import annotations
import random
from typing import Any, Dict, List, Tuple


# ── Action signature table ────────────────────────────────────────────────────
# base_effectiveness: P(full success) at ideal posture
# loudness:           network/operational signature footprint [0=silent, 1=loud]
# attrib_difficulty:  adversary counter-attribution friction [0=easy, 1=hard]
# active:             requires live network ops (botched = noisier)
ACTION_SIGNATURES: Dict[str, Dict[str, Any]] = {
    "isolate":            {"base_effectiveness": 0.85, "loudness": 0.55, "attrib_difficulty": 0.20, "active": True},
    "patch":              {"base_effectiveness": 0.90, "loudness": 0.30, "attrib_difficulty": 0.15, "active": False},
    "hunt":               {"base_effectiveness": 0.65, "loudness": 0.25, "attrib_difficulty": 0.10, "active": True},
    "deceive":            {"base_effectiveness": 0.70, "loudness": 0.10, "attrib_difficulty": 0.40, "active": False},
    "monitor":            {"base_effectiveness": 0.95, "loudness": 0.10, "attrib_difficulty": 0.05, "active": False},
    "block":              {"base_effectiveness": 0.80, "loudness": 0.35, "attrib_difficulty": 0.15, "active": False},
    "deploy":             {"base_effectiveness": 0.75, "loudness": 0.40, "attrib_difficulty": 0.20, "active": True},
    "restore":            {"base_effectiveness": 0.80, "loudness": 0.50, "attrib_difficulty": 0.25, "active": True},
    "scan":               {"base_effectiveness": 0.70, "loudness": 0.70, "attrib_difficulty": 0.30, "active": True},
    "rotate-credentials": {"base_effectiveness": 0.92, "loudness": 0.20, "attrib_difficulty": 0.10, "active": False},
    "evacuate":           {"base_effectiveness": 0.70, "loudness": 0.80, "attrib_difficulty": 0.50, "active": True},
    "unknown":            {"base_effectiveness": 0.40, "loudness": 0.30, "attrib_difficulty": 0.20, "active": False},
}

STEALTH_PENALTY = {"high": 0.30, "medium": 0.65, "low": 1.00}
STEALTH_MODIFIER = {"high": 1.0, "medium": 0.85, "low": 0.65}
RISK_MODIFIER    = {"low": 1.05, "medium": 1.0,  "high": 0.90}

# ── Effects library: action → (full, strong_partial, weak_partial, failure) ───
EFFECTS_LIBRARY: Dict[str, Tuple[List[str], List[str], List[str], List[str]]] = {
    "isolate": (
        ["[full] Target system fully segmented from OT network",
         "[full] Adversary C2 channel severed",
         "[full] Lateral movement to HMI-01 blocked"],
        ["[partial-strong] Segmentation applied — adversary C2 degraded but not severed",
         "[partial-strong] Jump host isolated; historian VLAN 42 path still reachable"],
        ["[partial-weak] Segmentation partial — historian still reachable via VLAN 42",
         "[partial-weak] Adversary may retain local persistence on jump host"],
        ["[failure] Isolation attempt detected and countered — adversary pivoted pre-cut",
         "[failure] Network change produced no effective segmentation"],
    ),
    "patch": (
        ["[full] CVE-2023-46805 remediated on VPN-GW",
         "[full] Initial access vector closed",
         "[full] Adversary lateral movement tooling blocked at perimeter"],
        ["[partial-strong] Patch applied to VPN-GW; downstream appliances queued",
         "[partial-strong] Primary re-entry vector closed — secondary vectors still open"],
        ["[partial-weak] Patch applied to VPN-GW only — downstream appliances still unpatched",
         "[partial-weak] Scheduled task persistence on JH-01 unaffected by patch"],
        ["[failure] Patch deployment failed — VPN-GW reverted to prior state",
         "[failure] Initial access vector remains open"],
    ),
    "hunt": (
        ["[full] Adversary scheduled task on JH-01 discovered and documented",
         "[full] Historian exfil staging directory identified",
         "[full] Full kill-chain mapped for attribution"],
        ["[partial-strong] Foothold on JH-01 confirmed; historian access extent unclear",
         "[partial-strong] Lateral movement artifacts found — HMI-01 staging unconfirmed"],
        ["[partial-weak] Hunt identified foothold on JH-01 but scope not fully mapped",
         "[partial-weak] Indicators found — analyst confidence insufficient for eviction order"],
        ["[failure] Hunt produced no actionable findings — adversary artifacts not located",
         "[failure] Adversary aware of hunt — counter-forensics likely in progress"],
    ),
    "deceive": (
        ["[full] Honeypot drew adversary away from HMI-01",
         "[full] Adversary interaction with decoy logged — TTPs captured",
         "[full] HMI-01 exposure window reduced by 60%"],
        ["[partial-strong] Honeypot engaged — adversary interaction logged, real assets less active",
         "[partial-strong] Deception partially effective; adversary divides attention between decoy and HIS-01"],
        ["[partial-weak] Honeypot partially engaged — adversary moved to decoy but retained HIS-01 access",
         "[partial-weak] Deception artifact planted; adversary has not yet interacted"],
        ["[failure] Deception infrastructure detected — adversary bypassing decoys entirely",
         "[failure] Honeypot timing anomalies burned the deception strategy"],
    ),
    "monitor": (
        ["[full] Enhanced logging active on all OT segments",
         "[full] Adversary beaconing pattern detected — C2 interval identified",
         "[full] Real-time alerting enabled for HMI-01 and HIS-01"],
        ["[partial-strong] Monitoring deployed on OT; SIEM ingestion lag ~2 min",
         "[partial-strong] Alerting active on primary assets; edge devices not yet covered"],
        ["[partial-weak] Monitoring deployed on IT segment; OT visibility still limited",
         "[partial-weak] Log ingestion lag of ~5 min — near-real-time, not real-time"],
        ["[failure] Monitoring deployment failed — agents not responsive on target hosts",
         "[failure] No additional visibility gained; existing logging gaps persist"],
    ),
    "block": (
        ["[full] Adversary egress IP blocked at FW-OT",
         "[full] Inbound VPN access from adversary subnet denied",
         "[full] Exfil channel disrupted"],
        ["[partial-strong] Primary egress IP blocked; adversary pivoting to alternate channel",
         "[partial-strong] Block effective at perimeter; internal pivot host not covered"],
        ["[partial-weak] Block applied at perimeter — adversary may pivot through compromised internal host",
         "[partial-weak] IP block effective; domain-fronting C2 variant not covered"],
        ["[failure] Block rule incorrectly applied — adversary traffic unaffected",
         "[failure] Firewall change reverted due to operational impact"],
    ),
    "deploy": (
        ["[full] EDR deployed to JH-01 and HIS-01",
         "[full] Deception grid live across OT VLAN",
         "[full] Capability operational — adversary activity now visible"],
        ["[partial-strong] EDR deployed to JH-01; historian deployment in progress",
         "[partial-strong] Capability live but alert tuning incomplete — elevated false positives"],
        ["[partial-weak] EDR deployed to JH-01; historian deployment queued for maintenance window",
         "[partial-weak] Capability staged but not fully tuned — high false-positive rate expected"],
        ["[failure] EDR deployment failed — incompatible OS version on target hosts",
         "[failure] Capability not operational; original visibility gap unchanged"],
    ),
    "restore": (
        ["[full] JH-01 reimaged — persistence removed",
         "[full] HIS-01 restored from known-good snapshot",
         "[full] Adversary evicted from both compromised hosts"],
        ["[partial-strong] JH-01 reimaged; HIS-01 restoration in progress from snapshot",
         "[partial-strong] Primary persistence evicted — root cause (VPN vuln) still open"],
        ["[partial-weak] JH-01 reimaged successfully; HIS-01 snapshot pre-dates latest config — data gap",
         "[partial-weak] System restored but root cause (VPN vuln) not yet remediated"],
        ["[failure] Restoration failed — snapshot integrity check failed, rollback aborted",
         "[failure] Systems remain in compromised state; adversary persistence intact"],
    ),
    "scan": (
        ["[full] Full OT network map generated",
         "[full] 3 additional unmanaged devices discovered on VLAN 10",
         "[full] Adversary staging directory fingerprinted"],
        ["[partial-strong] IT segment scanned; OT scan 60% complete — ICS disruption risk paused it",
         "[partial-strong] Partial asset inventory — key historians enumerated, HMIs pending"],
        ["[partial-weak] Scan completed on IT segment; OT scan paused to avoid ICS disruption",
         "[partial-weak] Partial asset inventory — historians and HMIs not fully enumerated"],
        ["[failure] Scan detected and actively interfered with — adversary feeding false port responses",
         "[failure] Network map produced unreliable — results should not be acted on"],
    ),
    "rotate-credentials": (
        ["[full] All service account credentials rotated",
         "[full] Adversary stolen credentials invalidated",
         "[full] MFA enforced on VPN-GW and jump host"],
        ["[partial-strong] Domain credentials rotated; local admin accounts on HIS-01 queued",
         "[partial-strong] Session tokens still valid for ~30 min — partial credential exposure window"],
        ["[partial-weak] Domain credentials rotated; local admin accounts on HIS-01 not yet updated",
         "[partial-weak] Credential rotation complete — session tokens may still be valid for up to 1 hour"],
        ["[failure] Credential rotation failed — directory sync error blocked propagation",
         "[failure] Adversary stolen credentials still valid; rotation window missed"],
    ),
    "evacuate": (
        ["[full] HMI-01 safely taken offline — grid control shifted to backup RTUs",
         "[full] Physical safety maintained — no load-shedding event",
         "[full] Adversary denied Stage 7 access window"],
        ["[partial-strong] HMI-01 offline; backup RTU coverage active for 4 of 6 substations",
         "[partial-strong] Manual control mode active — operational tempo reduced"],
        ["[partial-weak] HMI-01 offline — partial manual control mode active",
         "[partial-weak] Backup RTU coverage incomplete for substations 3 and 7"],
        ["[failure] Evacuation failed — HMI-01 unresponsive to shutdown command",
         "[failure] System remains online and adversary-accessible"],
    ),
    "unknown": (
        ["[full] Move executed — outcome uncertain",
         "[full] Recommend clarifying intent and resubmitting"],
        ["[partial-strong] Move partially executed — limited observable effect"],
        ["[partial-weak] Move attempted — effect scope unclear, minimal impact detected"],
        ["[failure] Move failed — action not recognized or could not be applied",
         "[failure] No defensive effect achieved"],
    ),
}

# ── Cascade library ───────────────────────────────────────────────────────────
# Each action has a baseline cascade string
CASCADE_BASELINE: Dict[str, str] = {
    "isolate":            "[severity:med] Adversary may detect isolation and accelerate timeline",
    "patch":              "[severity:low] Patch deployment requires 15-min maintenance window — coordinate with ops",
    "hunt":               "[severity:low] Hunt findings may trigger incident escalation to CISA",
    "deceive":            "[severity:low] Deception success may give false confidence — continue active monitoring",
    "monitor":            "[severity:low] Increased log volume may stress SIEM capacity",
    "block":              "[severity:med] Block may accelerate adversary pivot to alternative C2 channel",
    "deploy":             "[severity:low] EDR agent install may cause brief performance hit on OT historians",
    "restore":            "[severity:med] Restoration reveals pre-compromise state — adversary may reinfect if vuln open",
    "scan":               "[severity:med] Active scan may generate noise detectable by adversary",
    "rotate-credentials": "[severity:low] Rotation will lock out any Blue Team members using shared credentials",
    "evacuate":           "[severity:high] Offline HMI triggers automatic alarm in control room — prepare staff",
    "unknown":            "[severity:low] Move intent unclear — effect scope unconfirmed",
}

CASCADE_BY_OUTCOME: Dict[str, str] = {
    "full_success":    "[severity:low] Operational tempo favors Blue — adversary under increased pressure next turn",
    "strong_partial":  "[severity:med] Partial effect achieved — residual adversary capability, follow-up required",
    "weak_partial":    "[severity:med] Residual adversary capability — re-engagement expected within 1 turn",
    "failure":         "[severity:high] Adversary aware of attempt — defensive posture for this action class burned",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _target_fit(action: str, target: str, scenario: Dict[str, Any]) -> float:
    asset_status = {a["name"].upper(): a["status"] for a in scenario.get("assets", [])}
    t = target.upper()
    if t == "UNKNOWN":
        return 0.80
    fits = {
        ("patch",              "patching-pending"): 1.20,
        ("isolate",            "compromised"):      1.10,
        ("restore",            "compromised"):      1.10,
        ("hunt",               "compromised"):      1.10,
        ("evacuate",           "at-risk"):          1.15,
        ("evacuate",           "compromised"):      1.10,
        ("monitor",            "online"):           1.05,
        ("rotate-credentials", "compromised"):      1.10,
        ("block",              "online"):           1.05,
    }
    status = asset_status.get(t)
    if status:
        return fits.get((action, status), 1.00)
    return 1.00


def _sample_outcome(rng: random.Random, success_prob: float) -> str:
    p = success_prob
    weights = {
        "full_success":   p * p,
        "strong_partial": p * (1 - p),
        "weak_partial":   (1 - p) * p,
        "failure":        (1 - p) * (1 - p),
    }
    total = sum(weights.values())
    roll = rng.random()
    cumulative = 0.0
    for cls, w in weights.items():
        cumulative += w / total
        if roll <= cumulative:
            return cls
    return "failure"


def _build_cascades(
    action: str,
    outcome_class: str,
    detection_risk: float,
    attribution_risk: float,
) -> List[str]:
    cascades: List[str] = []
    cascades.append(CASCADE_BASELINE.get(action, "[severity:low] No baseline cascade identified"))
    cascades.append(CASCADE_BY_OUTCOME[outcome_class])
    if detection_risk > 0.60:
        cascades.append("[severity:high] OPSEC exposure — adversary may correlate Blue TTPs across turns")
    if attribution_risk > 0.50:
        cascades.append("[severity:high] Attribution exposure — diplomatic/legal escalation surface opened")
    if attribution_risk < 0.10 and outcome_class == "full_success":
        cascades.append("[severity:low] Low-attribution win — repeatable playbook if conditions hold")
    return cascades[:4]  # cap at 4 for readability


# ── Main entry point ──────────────────────────────────────────────────────────

def adjudicate(parsed: Dict[str, Any], scenario: Dict[str, Any], turn_id: int) -> Dict[str, Any]:
    action    = parsed.get("action", "unknown")
    stealth   = parsed.get("stealth_level", "medium")
    risk      = parsed.get("risk", "medium")
    confidence = parsed.get("confidence", 0.5)
    target    = parsed.get("target", "unknown")

    sig = ACTION_SIGNATURES.get(action, ACTION_SIGNATURES["unknown"])
    base_effectiveness = sig["base_effectiveness"]
    loudness           = sig["loudness"]
    attrib_difficulty  = sig["attrib_difficulty"]
    is_active          = sig["active"]

    rng = random.Random(turn_id * 31337 + hash(action) % 9999)

    # ── Stage 2: target fit ──────────────────────────────────────────────────
    tf = _target_fit(action, target, scenario)

    # ── Stage 3: composited success score ────────────────────────────────────
    effectiveness = base_effectiveness * tf
    execution     = STEALTH_MODIFIER.get(stealth, 1.0) * RISK_MODIFIER.get(risk, 1.0)
    preparation   = 0.50 + 0.50 * confidence          # confidence shifts variance, not mean center
    raw           = effectiveness * execution * preparation
    jitter        = rng.uniform(-0.06, 0.06)
    success_prob  = round(min(0.98, max(0.05, raw + jitter)), 2)

    # ── Stage 5: detection + attribution (conditional model) ─────────────────
    stealth_penalty = STEALTH_PENALTY.get(stealth, 0.65)
    botch_noise     = 0.10 if (is_active and rng.random() > success_prob) else 0.0
    detection_risk  = round(min(0.99, max(0.02,
        loudness * stealth_penalty + botch_noise + rng.uniform(-0.04, 0.04)
    )), 2)

    attrib_given_detect = round(min(0.95, max(0.05,
        (1.0 - attrib_difficulty) + rng.uniform(-0.03, 0.03)
    )), 2)
    attribution_risk = round(min(0.99, max(0.01,
        attrib_given_detect * detection_risk
    )), 2)

    # ── Stage 4: sample outcome class ────────────────────────────────────────
    outcome_class = _sample_outcome(rng, success_prob)

    # ── Effects selection ────────────────────────────────────────────────────
    full_fx, strong_fx, weak_fx, failure_fx = EFFECTS_LIBRARY.get(action, EFFECTS_LIBRARY["unknown"])
    effects_map = {
        "full_success":   full_fx,
        "strong_partial": strong_fx,
        "weak_partial":   weak_fx,
        "failure":        failure_fx,
    }
    effects = effects_map[outcome_class]

    # ── Stage 6: cascades ────────────────────────────────────────────────────
    cascading_effects = _build_cascades(action, outcome_class, detection_risk, attribution_risk)

    # ── Stage 7: rationale ───────────────────────────────────────────────────
    outcome_label = outcome_class.replace("_", " ")
    rationale = (
        f"Action '{action}' on '{target}': effectiveness {effectiveness:.2f} "
        f"(base {base_effectiveness:.2f} × target-fit {tf:.2f}), "
        f"execution {execution:.2f} (stealth={stealth}, risk={risk}), "
        f"preparation {preparation:.2f} (confidence {confidence:.0%}). "
        f"Outcome class: {outcome_label}. "
        f"Detection {detection_risk:.0%}, attribution {attribution_risk:.0%} "
        f"(P(attrib|detect)={attrib_given_detect:.0%})."
    )

    return {
        "success_probability": success_prob,
        "detection_risk":      detection_risk,
        "attribution_risk":    attribution_risk,
        "effects":             effects,
        "cascading_effects":   cascading_effects,
        "rationale":           rationale,
    }
