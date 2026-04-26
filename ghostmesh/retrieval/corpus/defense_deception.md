---
id: defense-deception
source: SANS ICS Security — Active Defense with Deception
tags: [defense, deception, honeypot, detection]
---
Deception technology in ICS environments offers a high signal-to-noise detection capability that complements passive monitoring. The core principle: deploy convincing fake assets (honeypot PLCs, fake historian entries, canary credentials, decoy HMI screens) that have no legitimate operational purpose — any interaction with them is a high-confidence indicator of adversary reconnaissance or intrusion.

In practice, ICS deception deployments include: honeypot Modbus/DNP3 endpoints configured to respond realistically to polling but alert on any write or control command; fake engineering workstation shares containing plausible-looking project files with canary document tracking; canary credentials (fake VPN accounts, fake historian service accounts) embedded in locations adversaries tend to discover during credential harvesting — Group Policy preferences, configuration files, browser saved passwords; and emulated PLC web interfaces that log every access.

The low false-positive rate makes deception alerts actionable — when a canary credential is used or a honeypot PLC receives an unexpected command, this justifies immediate incident response escalation without waiting for corroborating evidence. Deception is particularly effective against patient, stealthy actors like Volt Typhoon or Sandworm who conduct prolonged reconnaissance before taking action. Key implementation requirement: deception assets must be indistinguishable from real assets in terms of network behavior, banner strings, and protocol responses, or sophisticated adversaries will fingerprint and avoid them.
