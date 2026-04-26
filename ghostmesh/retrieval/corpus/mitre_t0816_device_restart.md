---
id: mitre-t0816
source: MITRE ATT&CK for ICS T0816 Device Restart/Shutdown
tags: [mitre, ics, impact, disruption]
---
T0816 Device Restart/Shutdown describes adversary actions that force ICS field devices — PLCs, RTUs, intelligent electronic devices (IEDs) — to restart or shut down, causing loss of view and loss of control over physical processes. Unlike IT environments where a server reboot is disruptive but recoverable, OT device restarts can cause uncontrolled physical-process transitions, equipment damage, or safety system failures.

Adversaries can trigger device restarts through multiple vectors: sending legitimate stop/restart commands over Modbus or DNP3 using compromised credentials, exploiting firmware vulnerabilities that cause device crashes, or using vendor-specific diagnostic commands accessible from engineering workstations. Some PLCs have web interfaces with default credentials that expose reboot functionality.

In the 2015 and 2016 Ukraine power grid attacks, threat actors used crafted serial commands over IEC 101 to force substation RTUs into non-responsive states, preventing operators from restoring breakers. Recovery time depended on physical dispatch of technicians. Detection strategies include: monitoring for unexpected state transitions (RUN → STOP) on PLCs, alerting on device restart events in SCADA audit logs, and detecting unusual engineering workstation connections to field devices outside of maintenance windows.
