---
id: csis-volt-typhoon
source: CSIS — Volt Typhoon Critical Infrastructure Pre-Positioning Analysis (2024)
tags: [csis, analysis, prepositioning, escalation, apt]
---

CSIS analysis of Volt Typhoon operations identifies a pre-positioning strategy distinct from traditional espionage: the goal is not data exfiltration but persistent access to US critical infrastructure for potential activation during a geopolitical crisis. CISA, NSA, and FBI confirmed Volt Typhoon maintained access to US communications, energy, and water sector networks for up to five years before discovery.

Key adversary behavior patterns: living-off-the-land (LOLBins) to minimize malware footprint; compromised SOHO routers as relay nodes to obscure C2 origin; multi-stage lateral movement through IT to OT convergence points; targeting of Operational Technology (OT) historian and HMI systems specifically.

Escalation indicator: Volt Typhoon TTPs shift from passive access maintenance to active staging when geopolitical tension indicators rise (Taiwan Strait, South China Sea incidents). Pre-positioning escalates to pre-impact staging when HMI/RTU access paths are established. Blue Team detection of LOLBin activity near OT convergence points should be treated as Stage 6 equivalent regardless of absence of active malicious commands.

Strategic framing: access is the deterrent. Volt Typhoon's value to PRC decision-makers is the credible capability to disrupt infrastructure, not the execution of disruption. This changes eviction calculus — eviction without public attribution may not deter re-entry.
