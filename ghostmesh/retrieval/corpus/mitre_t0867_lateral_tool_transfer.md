---
id: mitre-t0867
source: MITRE ATT&CK for ICS T0867 Lateral Tool Transfer
tags: [mitre, ics, lateral-movement]
---
T0867 Lateral Tool Transfer describes adversaries moving attack tools, scripts, and malware from IT network footholds into OT network segments using file transfer mechanisms that traverse the IT/OT boundary. Because direct internet access from OT networks is typically blocked, adversaries must bridge through intermediate systems.

Common transfer paths exploit legitimate data flows: historians and SCADA servers that synchronize data between IT and OT networks, shared file servers accessible from both DMZ and OT zones, removable media (USB) brought in by engineers, and vendor remote access channels. Engineering workstations are particularly vulnerable — they routinely transfer project files between corporate laptops and OT systems, creating an approved channel that adversaries can abuse.

Sandworm used this technique in the 2022 Industroyer2 attack, staging tooling through the compromised SCADA server before deploying ICS-specific payloads to substation IEDs. PIPEDREAM components were similarly transferred via legitimate OPC UA connections. Defenses include application whitelisting on engineering workstations and historian servers, USB device control policies, monitoring for unexpected executable files in OT file system paths, and ensuring IT/OT file share connections are one-directional where possible. Any executable appearing in an OT system outside of a formal change management process should be treated as a high-severity indicator of compromise.
