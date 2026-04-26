---
id: jcs-jp3-28
source: Joint Chiefs of Staff — JP 3-28 Defense Support of Civil Authorities (2021), Annex B
tags: [doctrine, jcs, dsca, resilience, escalation]
---

JP 3-28 Annex B addresses Defense Support of Civil Authorities (DSCA) for critical infrastructure incidents. When a cyber incident threatens national critical infrastructure (energy, water, transportation), the DoD provides support to lead federal agencies (CISA, FBI, DOE) under the National Response Framework.

Key trigger: DoD cyber support to critical infrastructure is activated when: (1) the incident exceeds civilian response capacity, (2) there is attribution to a foreign state actor, or (3) physical safety of civilians is threatened. ICS impact crossing into load-shedding, water treatment failure, or pipeline rupture automatically triggers DSCA authority review.

Blue Team doctrinal responsibility: preserve forensic evidence before eviction. Evidence required for DSCA activation includes host-based artifacts (scheduled tasks, registry keys, memory dumps), network captures (C2 traffic, lateral movement), and configuration change logs. Evicting an adversary without preserving evidence delays DSCA authority activation and inter-agency response.

Immediate notification requirements: upon detection of Stage 6-equivalent adversary activity (pre-impact staging near HMI/RTU), immediate notification to CISA and sector ISAC is required. Do not wait for eviction to complete before notifying.
