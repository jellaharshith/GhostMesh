---
id: concept-persistence
source: ICS Persistence Mechanisms — MITRE ATT&CK for ICS
tags: [concept, persistence, ics]
---
Persistence in ICS environments refers to mechanisms adversaries use to maintain access across reboots, credential changes, software updates, and partial incident response actions. Unlike IT environments where persistence often involves registry run keys or scheduled tasks, ICS persistence mechanisms extend into the firmware and logic layers of OT devices — making detection and removal significantly more difficult.

Primary persistence methods include: valid accounts (T0859) — using legitimate credentials that survive credential resets if not all accounts are rotated; modified PLC/RTU firmware — malicious code inserted into device firmware survives a PLC program wipe and requires full firmware reflash with a vendor-verified image; modified PLC ladder logic — malicious subroutines in PLC programs survive host OS reimaging since they reside on the PLC itself; webshells on historian or SCADA web servers; and scheduled tasks or services on engineering workstations.

The critical lesson from incident response: conventional IR actions (malware removal, process termination, host reimaging) are insufficient if persistence exists at the firmware or PLC logic layer. Full recovery requires: verified reimaging of all host systems using offline gold images, validated reflash of PLC/RTU firmware using vendor-provided and cryptographically verified images, comparison of all restored PLC logic against known-good backups, and credential rotation across the entire OT environment. Failure to address firmware or PLC-layer persistence has led to reinfection within 72 hours in documented ICS incidents.
