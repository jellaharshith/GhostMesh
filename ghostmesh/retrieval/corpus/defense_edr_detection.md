---
id: defense-edr
source: CISA Guidance — Endpoint Detection for ICS
tags: [defense, edr, detection, monitoring]
---
Deploying endpoint detection and response (EDR) in ICS/OT environments presents unique challenges compared to enterprise IT: engineering workstations frequently run legacy operating systems (Windows XP, Windows 7) that are unsupported by modern EDR agents; many OT hosts cannot tolerate the CPU/memory overhead of real-time scanning without risking process disruption; and air-gapped systems cannot use cloud-based threat intelligence feeds.

The recommended approach is a phased deployment: begin with passive network-based monitoring (OT-aware IDS using tools like Dragos, Claroty, or open-source Zeek with ICS protocol parsers) to build an asset inventory and baseline normal communication patterns before any endpoint agent deployment. This provides detection capability without endpoint risk.

Where EDR agents are deployable (modern engineering workstations, historian servers), configure them in audit/observe mode initially to validate performance impact. Key detections to prioritize: new or modified executables appearing on engineering workstations; unexpected parent-child process relationships (e.g., TIA Portal spawning cmd.exe); off-hours logins to historian servers; unexpected network connections from PLC programming software to non-PLC destinations; and anomalous Modbus function codes (FC08 diagnostics, FC23 read/write) sourced from non-engineering hosts. Behavioral baselining over 30-90 days before enabling blocking modes is essential to avoid false-positive-driven operational disruptions.
