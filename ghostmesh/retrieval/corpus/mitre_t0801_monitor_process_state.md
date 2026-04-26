---
id: mitre-t0801
source: MITRE ATT&CK for ICS T0801 Monitor Process State
tags: [mitre, ics, monitoring, collection]
---
Adversaries executing T0801 Monitor Process State collect real-time sensor readings, setpoint values, historian logs, and alarm states from ICS environments to build situational awareness before executing disruptive or destructive operations. By observing process variables — pressure, temperature, flow rate, valve positions — an attacker can understand normal operating envelopes, identify safe windows for manipulation, and avoid premature detection.

In ICS environments this is particularly dangerous because process state data is often transmitted over unauthenticated protocols such as Modbus TCP, DNP3, and OPC-DA. An adversary with network access can passively monitor these communications without any credentials. Combined with historian databases (OSIsoft PI, Wonderware), attackers gain longitudinal process records that reveal maintenance cycles and shift patterns.

T0801 is frequently observed as a precursor to impact techniques — operators who monitor state first are better positioned to time an attack (e.g., during a peak load period for a power utility or during a critical batch cycle in a chemical plant). Detection requires baselining which systems legitimately poll process data and alerting on unexpected polling sources or unusual query volumes on SCADA historian ports (TCP 5450, 102).
