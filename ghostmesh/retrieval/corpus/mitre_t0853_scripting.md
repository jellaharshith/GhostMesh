---
id: mitre-t0853
source: MITRE ATT&CK for ICS T0853 Scripting
tags: [mitre, ics, execution]
---
T0853 Scripting in ICS environments describes adversaries leveraging native OT scripting capabilities — PLC ladder logic modifications, structured text (ST) programs, vendor-supplied automation scripts, and HMI scripting environments — to execute malicious code and maintain persistence within OT systems. Unlike IT environments where attackers use PowerShell or bash, ICS attackers exploit the built-in programmability of control systems.

Engineering workstations running Siemens TIA Portal, Rockwell Studio 5000, or Schneider EcoStruxure provide rich scripting environments with direct PLC programming access. An adversary who compromises an engineering workstation can push modified ladder logic that executes malicious subroutines on every PLC scan cycle — typically every 10-100 milliseconds. These modifications survive PLC power cycles and are indistinguishable from legitimate logic changes without detailed code review.

PIPEDREAM/INCONTROLLER malware modules demonstrated automated PLC logic manipulation via Modbus and OPC UA, scripting reconnaissance, parameter modification, and shutdown sequences. Defenses include: code-signing for PLC program uploads, version control for all ladder logic with diff alerting on unexpected changes, restricting engineering workstation network access to only required PLC addresses, and periodic integrity verification of PLC code against known-good images stored offline.
