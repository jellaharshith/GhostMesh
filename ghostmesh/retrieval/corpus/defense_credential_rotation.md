---
id: defense-credential-rotation
source: NSA/CISA Advisory — Mitigating Living Off the Land
tags: [defense, credentials, mitigation]
---
Credential rotation in ICS environments is a critical mitigation that must be carefully orchestrated to avoid operational disruption. Many OT systems have hard-coded or shared credentials embedded in control system configurations, historian connection strings, and vendor remote access portals — rotation requires coordinated updates across multiple interdependent systems.

The NSA/CISA advisory on mitigating living-off-the-land techniques (targeting Volt Typhoon and similar actors) specifically recommends: immediately rotating all VPN, remote access, and jump server credentials following any suspected or confirmed intrusion; rotating all service account credentials used by historian synchronization, SCADA data acquisition, and OT monitoring platforms; and auditing for shared accounts (single credentials used by multiple personnel or systems) which are common in legacy ICS deployments for operational convenience but create unattributable access and complicate rotation.

Phased rotation — changing credentials in a test environment first, validating connectivity, then rolling production — avoids the scenario where simultaneous rotation causes a cascade of authentication failures on OT systems. Multi-factor authentication must be enforced on all remote access paths; hardware tokens (FIDO2/PIV) are preferred over SMS-based MFA due to SIM-swapping risks. Privileged Access Workstations (PAWs) — dedicated, hardened systems used exclusively for OT administrative tasks — prevent credential theft via browser-based attacks or lateral movement from general-purpose corporate machines.
