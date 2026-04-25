"""
Red Cell: rule-based adversary response.
Adapts to Blue action and adjudication outcome — not random, not always-escalate.
"""
from __future__ import annotations
import random
from typing import Any, Dict


# ── Response playbook ────────────────────────────────────────────────────────
# Keyed by (blue_action, escalation_tier) → response template
# escalation_tier derived from detection_risk + attribution_risk thresholds

RESPONSE_PLAYBOOK: Dict[str, Dict[str, Dict[str, str]]] = {
    "isolate": {
        "retreat":   {
            "red_action":  "Suspend C2 beaconing and maintain dormant persistence",
            "target":      "JH-01 scheduled task",
            "intent":      "Avoid detection by reducing network noise during isolation event",
            "rationale":   "Blue isolation detected — going dark to preserve foothold. Await lower-noise window.",
        },
        "hold": {
            "red_action":  "Pivot C2 to out-of-band channel via compromised email account",
            "target":      "HIS-01 outbound SMTP relay",
            "intent":      "Maintain persistence through alternate C2 while primary channel is disrupted",
            "rationale":   "Primary C2 severed by isolation. Email exfil channel pre-staged — activating.",
        },
        "escalate": {
            "red_action":  "Accelerate lateral movement toward HMI-01 before segmentation hardens",
            "target":      "HMI-01 via ENG-WS-1 relay",
            "intent":      "Achieve Stage 7 foothold before Blue completes network hardening",
            "rationale":   "Window closing. Moving to HMI-01 now using pre-staged tooling on ENG-WS-1.",
        },
    },
    "patch": {
        "retreat": {
            "red_action":  "Shift reliance from VPN exploit to existing persistence on JH-01",
            "target":      "JH-01 scheduled task",
            "intent":      "Re-entry vector closed — depend on existing foothold until new vector found",
            "rationale":   "VPN access patched. Falling back to already-established persistence.",
        },
        "hold": {
            "red_action":  "Stage secondary access via supply-chain vendor VPN credentials",
            "target":      "FW-OT vendor management port",
            "intent":      "Establish backup entry vector through third-party access",
            "rationale":   "Primary entry closed. Activating pre-identified vendor credential set.",
        },
        "escalate": {
            "red_action":  "Deploy wiper pre-stage on HIS-01 as leverage before patch hardens position",
            "target":      "HIS-01 historian data store",
            "intent":      "Establish destructive deterrent to complicate Blue remediation decision",
            "rationale":   "Blue patching aggressively. Staging wiper payload for deterrence / Stage 6 hold.",
        },
    },
    "hunt": {
        "retreat": {
            "red_action":  "Wipe artifacts from JH-01 and rotate implant to fileless variant",
            "target":      "JH-01 disk artifacts",
            "intent":      "Deny forensic evidence and reset detection baseline",
            "rationale":   "Hunt activity detected. Burning current foothold, transitioning to fileless implant.",
        },
        "hold": {
            "red_action":  "Plant false flag artifacts pointing to unrelated nation-state group",
            "target":      "JH-01 and HIS-01 event logs",
            "intent":      "Confuse attribution and buy operational time",
            "rationale":   "Blue hunting with intent to attribute. Seeding false IOCs to misdirect.",
        },
        "escalate": {
            "red_action":  "Accelerate exfiltration of historian configuration data before eviction",
            "target":      "HIS-01 config export",
            "intent":      "Collect maximum intelligence before foothold is lost",
            "rationale":   "Hunt will likely lead to eviction. Prioritizing exfil of ICS engineering data.",
        },
    },
    "deceive": {
        "retreat": {
            "red_action":  "Avoid honeypot — restrict activity to known-good target paths",
            "target":      "HMI-01 direct",
            "intent":      "Operate only on confirmed real assets to avoid deception infrastructure",
            "rationale":   "Deception infrastructure detected via timing anomalies. Avoiding flagged hosts.",
        },
        "hold": {
            "red_action":  "Interact minimally with decoy to probe Blue deception strategy",
            "target":      "Honeypot node",
            "intent":      "Map Blue deception coverage while limiting exposure",
            "rationale":   "Engaging honeypot cautiously to understand Blue TTPs without triggering full response.",
        },
        "escalate": {
            "red_action":  "Use deception infrastructure as distraction — simultaneous move on HMI-01",
            "target":      "HMI-01 while Blue watches honeypot",
            "intent":      "Split Blue attention between decoy and real objective",
            "rationale":   "Blue invested in honeypot defense — exploiting divided attention for real-asset access.",
        },
    },
    "monitor": {
        "retreat": {
            "red_action":  "Drop beacon frequency to once per 6 hours to evade threshold alerts",
            "target":      "JH-01 C2 channel",
            "intent":      "Stay below monitoring alert thresholds",
            "rationale":   "Increased logging detected. Reducing C2 cadence to avoid statistical detection.",
        },
        "hold": {
            "red_action":  "Shift to living-off-the-land techniques using native Windows tools",
            "target":      "JH-01 and HIS-01",
            "intent":      "Blend with legitimate admin activity to evade enhanced monitoring",
            "rationale":   "EDR/logging active. Switching to LOLBins — WMI, PowerShell, certutil.",
        },
        "escalate": {
            "red_action":  "Exfiltrate historian data via encrypted DNS tunnel before monitoring matures",
            "target":      "HIS-01 → external DNS resolver",
            "intent":      "Complete primary intelligence objective before detection capability fully operational",
            "rationale":   "Monitoring not yet mature. Exploiting gap to complete exfil objective.",
        },
    },
    "block": {
        "retreat": {
            "red_action":  "Suspend operations and await intelligence on Blue firewall ruleset",
            "target":      "All current C2 channels",
            "intent":      "Understand scope of Blue blocking before committing to alternate path",
            "rationale":   "Block rules unknown scope. Pausing to avoid burning remaining infrastructure.",
        },
        "hold": {
            "red_action":  "Pivot C2 to domain-fronted HTTPS through CDN infrastructure",
            "target":      "CDN-masked C2 endpoint",
            "intent":      "Bypass IP-based blocking via domain fronting",
            "rationale":   "IP block active. Activating domain-fronted C2 variant — CDN endpoint pre-staged.",
        },
        "escalate": {
            "red_action":  "Establish persistence via legitimate cloud sync service (OneDrive) for C2",
            "target":      "ENG-WS-1 OneDrive client",
            "intent":      "Use trusted cloud service to bypass perimeter blocks",
            "rationale":   "Traditional C2 blocked. Moving to cloud-based C2 using legitimate service.",
        },
    },
    "deploy": {
        "retreat": {
            "red_action":  "Disable implant on newly-covered hosts and shift to uncovered assets",
            "target":      "ENG-WS-1 (no EDR coverage detected)",
            "intent":      "Move laterally away from newly instrumented hosts",
            "rationale":   "EDR deployment pattern observed. Pivoting to hosts not yet covered.",
        },
        "hold":    {
            "red_action":  "Tamper with EDR configuration to reduce telemetry fidelity",
            "target":      "JH-01 EDR agent config",
            "intent":      "Degrade Blue visibility while maintaining presence",
            "rationale":   "EDR active but config may be editable. Attempting to reduce logging verbosity.",
        },
        "escalate": {
            "red_action":  "Deploy destructive payload trigger on HIS-01 ahead of eviction",
            "target":      "HIS-01 historian data store",
            "intent":      "Establish leverage — threaten data destruction to deter Blue eviction",
            "rationale":   "Blue expanding capability rapidly. Staging payload for escalation leverage.",
        },
    },
    "restore": {
        "retreat": {
            "red_action":  "Accept loss of current foothold — await opportunity to reinfect via VPN",
            "target":      "VPN-GW (if unpatched)",
            "intent":      "Preserve capability by not burning unpatched vector in response",
            "rationale":   "Foothold lost to reimage. If VPN still unpatched, reentry possible.",
        },
        "hold": {
            "red_action":  "Reinfect restored system via same vector within maintenance window",
            "target":      "JH-01 post-reimage",
            "intent":      "Re-establish persistence before vulnerability is patched",
            "rationale":   "System restored but root cause open. Re-exploiting VPN within detection gap.",
        },
        "escalate": {
            "red_action":  "Execute Stage 6 payload — disrupt historian data integrity before eviction completes",
            "target":      "HIS-01 historian database",
            "intent":      "Inflict maximum impact before Blue fully evicts presence",
            "rationale":   "Eviction imminent. Executing data integrity attack as final operational act.",
        },
    },
    "scan": {
        "retreat": {
            "red_action":  "Detect scan traffic and go silent for 24 hours",
            "target":      "All active implants",
            "intent":      "Avoid being fingerprinted during active Blue scan",
            "rationale":   "Active scan detected via network traffic spike. Going dark to avoid enumeration.",
        },
        "hold": {
            "red_action":  "Feed false open ports to confuse Blue asset inventory",
            "target":      "JH-01 network interface",
            "intent":      "Corrupt Blue's network map with honeyed port responses",
            "rationale":   "Blue scanning. Opening phantom ports to pollute their inventory.",
        },
        "escalate": {
            "red_action":  "Use Blue scan timing as cover noise to exfiltrate historian config",
            "target":      "HIS-01",
            "intent":      "Blend exfil traffic with Blue-generated scan traffic",
            "rationale":   "Blue scan creating noise. Using traffic cover to execute exfil.",
        },
    },
    "rotate-credentials": {
        "retreat": {
            "red_action":  "Accept credential loss — rely on API key cached in historian service account",
            "target":      "HIS-01 service account",
            "intent":      "Survive credential rotation via pre-cached non-rotating credential",
            "rationale":   "Credentials rotated. Checking for cached API keys / non-rotating service tokens.",
        },
        "hold": {
            "red_action":  "Capture new credentials during post-rotation authentication with keylogger",
            "target":      "JH-01 admin session",
            "intent":      "Re-acquire credentials via keylogger already installed on jump host",
            "rationale":   "Credentials rotated but keylogger still active on JH-01. Capturing new creds.",
        },
        "escalate": {
            "red_action":  "Use token replay against active admin session before rotation completes",
            "target":      "Active VPN session token",
            "intent":      "Exploit session token validity window post-credential rotation",
            "rationale":   "Session tokens valid for up to 1 hour post-rotation. Exploiting window.",
        },
    },
    "evacuate": {
        "retreat": {
            "red_action":  "Stand down — objective window closed, preserve remaining infrastructure",
            "target":      "All current footholds",
            "intent":      "Avoid operational exposure when primary target offline",
            "rationale":   "HMI-01 offline — Stage 7 window closed. Preserving capability for future op.",
        },
        "hold": {
            "red_action":  "Maintain persistence on HIS-01 and await HMI-01 restoration",
            "target":      "HIS-01",
            "intent":      "Wait for HMI to come back online before proceeding with ICS impact",
            "rationale":   "HMI offline temporarily. Holding position for restoration window.",
        },
        "escalate": {
            "red_action":  "Target backup RTU infrastructure during gap created by HMI evacuation",
            "target":      "Backup RTU VLAN",
            "intent":      "Exploit control gap during manual operations mode",
            "rationale":   "HMI offline — backup RTUs now primary control. Targeting less-protected RTU segment.",
        },
    },
    "unknown": {
        "retreat": {
            "red_action":  "Monitor Blue activity pattern before committing to response",
            "target":      "Blue Team network activity",
            "intent":      "Gather intelligence on Blue intent before acting",
            "rationale":   "Blue action unclear. Holding to avoid premature exposure.",
        },
        "hold": {
            "red_action":  "Continue current operation unchanged",
            "target":      "Existing footholds",
            "intent":      "Maintain steady-state until Blue intent is clearer",
            "rationale":   "Blue action ambiguous. No change to operational posture.",
        },
        "escalate": {
            "red_action":  "Accelerate exfiltration while Blue posture is unclear",
            "target":      "HIS-01",
            "intent":      "Exploit Blue confusion to advance primary objective",
            "rationale":   "Blue posture ambiguous — opportunity window. Advancing exfil.",
        },
    },
}


def _escalation_tier(detection_risk: float, attribution_risk: float, blue_action: str) -> str:
    combined = (detection_risk + attribution_risk) / 2
    if combined >= 0.55:
        return "retreat"
    if combined >= 0.30:
        if blue_action in ("restore", "evacuate"):
            return "escalate"
        return "hold"
    return "escalate"


ESCALATION_LABEL_MAP = {
    "retreat":             "retreat",
    "hold":                "hold",
    "escalate":            "escalate",
}

ESCALATION_DESTRUCTIVE_THRESHOLD = 0.15


def generate_red_response(
    parsed: Dict[str, Any],
    adjudication: Dict[str, Any],
    scenario: Dict[str, Any],
    turn_id: int,
) -> Dict[str, Any]:
    action = parsed.get("action", "unknown")
    detection_risk = adjudication.get("detection_risk", 0.3)
    attribution_risk = adjudication.get("attribution_risk", 0.1)
    success_prob = adjudication.get("success_probability", 0.5)

    tier = _escalation_tier(detection_risk, attribution_risk, action)

    # High success prob for Blue and low detection → adversary under pressure → may escalate
    if success_prob >= 0.80 and detection_risk < 0.25:
        tier = "escalate"

    playbook = RESPONSE_PLAYBOOK.get(action, RESPONSE_PLAYBOOK["unknown"])
    response = playbook.get(tier, playbook["hold"])

    # Determine escalation_level label
    if tier == "escalate" and action in ("restore", "evacuate", "patch"):
        escalation_level = "escalate_destructive"
    else:
        escalation_level = tier

    return {
        "red_action":      response["red_action"],
        "target":          response["target"],
        "intent":          response["intent"],
        "escalation_level": escalation_level,
        "rationale":       response["rationale"],
    }
