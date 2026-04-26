---
id: csis-sandworm-industroyer2
source: CSIS — Sandworm / Industroyer2 Ukraine Grid Attack Post-Mortem (2023)
tags: [csis, analysis, escalation, ics, apt, grid]
---

CSIS post-mortem of the April 2022 Industroyer2 attack against Ukrainian power infrastructure identifies Sandworm's operational pattern: multi-stage compromise beginning 6–8 months prior, culminating in coordinated simultaneous payload deployment against substation protection relays timed to maximize impact.

Key CSIS finding: the attack was preceded by a failed first attempt in February 2022 that was detected and partially remediated. Sandworm adapted and rebuilt access without Blue detecting the re-entry. This confirms: eviction without complete root cause remediation leads to reinfection within weeks.

Adversary decision calculus from CSIS analysis: Sandworm accepted high detection risk for Industroyer2 because geopolitical context (active conflict) changed the cost-benefit calculation. In peacetime, Sandworm prefers low-profile persistent access. Crisis conditions activate destructive capabilities. Blue Teams should treat crisis onset (e.g., sanctions, military mobilization) as an indicator for adversary transition from Stage 5 to Stage 7 posture.

Escalation framing: destructive capability deployment is not a technical decision; it is a political decision. Sandworm only deploys destructive payloads when authorized by GRU leadership in response to strategic direction. This means escalation to destructive tier correlates with geopolitical crisis intensity, not purely Blue Team pressure.
