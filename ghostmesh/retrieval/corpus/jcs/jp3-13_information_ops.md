---
id: jcs-jp3-13
source: Joint Chiefs of Staff — JP 3-13 Information Operations (2023)
tags: [doctrine, jcs, deception, posture, escalation]
---

JP 3-13 frames military deception (MILDEC) as a core information operations capability. Deception operations create false impressions in the adversary decision-maker's mind to cause them to take (or not take) action. In defensive cyber contexts, deception infrastructure — honeypots, decoy assets, false network topologies — serves as both an intelligence collection mechanism and a cost-imposition tool.

Key principle: deception must be tied to a specific adversary decision. Deploying a decoy without a defined "desired adversary action" reduces its operational value. Effective honeypot operations require Blue to monitor adversary interaction in near-real-time and correlate captured TTPs against known threat libraries.

Counter-deception: adversaries skilled in MILDEC will probe decoys for timing anomalies and response signatures before committing. Red cells following disciplined tradecraft will test honeypot response latency (typically >50ms for virtualized nodes) and compare file system metadata patterns against known production baselines. Blue must minimize honeypot artifact discoverability.

Escalation risk: overt deception infrastructure discovery by the adversary burns the deception strategy and may accelerate offensive action.
