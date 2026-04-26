---
id: apt-sandworm
source: ESET Research — Industroyer/Crashoverride
tags: [apt, russia, ics, impact, power-grid]
---
Sandworm (attributed to GRU Unit 74455) is Russia's most destructive cyber threat actor, responsible for the BlackEnergy attacks on Ukrainian power infrastructure (2015, 2016), NotPetya (2017), and the Industroyer2 attack on Ukrainian high-voltage substations (April 2022).

Industroyer (2016) and its successor Industroyer2 (2022) are purpose-built ICS malware frameworks — the most sophisticated since Stuxnet — designed specifically to interact with electrical substation equipment using native ICS protocols. Industroyer contained modular payload components for IEC 60870-5-101 (serial), IEC 60870-5-104 (TCP), IEC 61850, and OPC DA protocols, enabling it to send unauthorized control commands directly to protection relays and breakers without going through legitimate HMI software.

The 2016 attack caused approximately 75 MWh of outage in Kyiv by opening breakers across multiple substations simultaneously. Critically, Industroyer also deployed a wiper payload targeting the SCADA server's Windows registry and industrial communication files, extending recovery time by preventing operators from using the control system to restore the grid. Industroyer2 was a more targeted, hardcoded variant deployed against a specific Ukrainian high-voltage transmission substation in 2022, coordinated with the Sandworm CaddyWiper malware. Defenses: OT protocol anomaly detection, IED firmware integrity monitoring, and offline backup of substation configuration files and PLC programs.
