---
id: concept-lateral-movement
source: Cyber Kill Chain / ICS Lateral Movement Concepts
tags: [concept, lateral-movement, ics]
---
Lateral movement in ICS environments describes the progression of an adversary from initial access — typically in the IT enterprise network — through successive network segments until they achieve access to operational technology systems capable of affecting physical processes. The typical attack path follows the Purdue model levels in reverse: internet/enterprise IT (Level 4) → corporate network → DMZ/historian (Level 3.5/3) → SCADA server → engineering workstation (Level 2) → PLC/RTU (Level 1) → field devices (Level 0).

Key chokepoints that defenders must monitor are the IT/OT boundary transitions. Common lateral movement techniques observed in ICS intrusions include: credential reuse from IT to OT accounts (many organizations mirror AD credentials into ICS), exploitation of historian servers as dual-homed pivot points, abuse of vendor remote access channels as a path that bypasses normal segmentation, and USB-mediated movement in fully air-gapped environments.

Detection requires east-west traffic monitoring within OT segments (not just north-south perimeter monitoring), behavioral baselining of which systems communicate with which (an HMI that suddenly connects to an adjacent PLC it has never previously polled is anomalous), and process-level monitoring on engineering workstations for unexpected application launches or network connections. Dwell time in ICS intrusions is often measured in months — Sandworm and Volt Typhoon both demonstrated multi-month persistence before executing effects.
