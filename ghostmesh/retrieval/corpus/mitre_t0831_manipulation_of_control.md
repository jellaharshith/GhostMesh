---
id: mitre-t0831
source: MITRE ATT&CK for ICS T0831 Manipulation of Control
tags: [mitre, ics, impact]
---
T0831 Manipulation of Control describes adversaries sending unauthorized commands to ICS field devices to alter the state of physical processes. This is a high-impact technique because it directly translates cyber actions into physical-world consequences — opening or closing valves, starting or stopping motors, enabling or disabling safety interlocks.

Unlike T0836 (Modify Parameter) which changes setpoints, T0831 involves direct command injection: issuing Modbus Write Coil (FC01/FC05), DNP3 Direct Operate, or IEC 61850 GOOSE control messages that immediately actuate field devices. Adversaries must first understand the process topology to issue commands that cause meaningful disruption without immediate safety system intervention.

Stuxnet demonstrated the pinnacle of T0831 — it reprogrammed Siemens S7-315 PLCs to alternate centrifuge speeds while reporting normal status to operators. The Triton/TRISIS malware targeted Schneider Triconex safety PLCs, attempting to disable safety instrumented systems so that a concurrent manipulation attack could cause an uncontrolled physical event. Defense requires strict whitelisting of command sources (only authorized HMIs can send control commands), OT-aware deep packet inspection to detect unexpected command types or out-of-range values, and independent safety layer validation.
