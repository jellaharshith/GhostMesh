---
id: concept-purdue
source: Purdue Enterprise Reference Architecture for ICS
tags: [concept, architecture, ics, segmentation]
---
The Purdue Enterprise Reference Architecture (PERA) defines a hierarchical model for ICS network organization that remains the foundational reference for OT security design despite being developed in the 1990s. The model defines distinct levels with security implications at each boundary.

Level 0 contains physical field devices: sensors, actuators, motors, valves — the instruments that interact with the physical process. Level 1 contains controllers: PLCs, RTUs, and DCS controllers that execute control logic and interface with Level 0 devices via fieldbus protocols (PROFIBUS, DeviceNet, HART). Level 2 contains SCADA systems, HMIs, and control room workstations that provide operator visualization and control input. Level 3 contains site operations systems: historians (OSIsoft PI), manufacturing execution systems (MES), and engineering workstations used for PLC programming. Level 3.5 is the IT/OT DMZ — the critical security boundary — containing mirror historians, data aggregation servers, remote access jump hosts, and application proxies. Level 4 contains enterprise IT: corporate ERP, email, business intelligence systems.

The security principle is that communication should be restricted to adjacent levels and minimized at each crossing. The Level 3.5 DMZ should enforce strict policies: data may flow upward (OT→IT) via one-directional mechanisms, but management traffic from IT into OT must route through authenticated, audited jump servers. Every inter-level communication path is an attack surface. Network diagrams should explicitly document all approved cross-level flows, and any undocumented path represents a segmentation gap.
