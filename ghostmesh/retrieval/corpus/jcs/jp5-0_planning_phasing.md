---
id: jcs-jp5-0
source: Joint Chiefs of Staff — JP 5-0 Joint Planning (2020), Chapter IV
tags: [doctrine, jcs, phasing, planning, posture]
---

JP 5-0 establishes the Joint Operation Planning Process (JOPP). For cyber-focused operations, key planning considerations include: mission analysis of adversary objectives (what does the adversary intend to achieve?), center of gravity identification (what capability enables adversary operations?), and lines of effort.

In ICS/OT defense planning: the adversary center of gravity is typically persistent access to engineering workstations and HMI nodes, not initial access vectors. Planners must design defensive lines of effort toward the adversary's objective, not just their current position.

Course of action (COA) development for defensive cyber: each COA must address all adversary access paths simultaneously. Patching VPN without addressing existing persistence is an incomplete COA and will fail adjudication. Full success requires closing both the access vector and the existing foothold in the same planning window.

Sequencing: isolate before hunt (sequencing matters — hunting before isolation tips the adversary to Blue's detection capability). Restore after patch (reimaging without closing the reinfection path is wasted effort). Doctrinal sequence: Monitor → Hunt → Isolate → Patch → Rotate Credentials → Restore.
