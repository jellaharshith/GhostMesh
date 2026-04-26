---
id: defense-segmentation
source: ICS-CERT Recommended Practice — Defense in Depth
tags: [defense, segmentation, ics, architecture]
---
Network segmentation is the foundational defense for ICS environments, structured around the Purdue Enterprise Reference Architecture. The core principle is that communication between network levels must be strictly controlled, and IT-to-OT traffic should be denied by default with only specific, approved flows permitted through a hardened DMZ.

Recommended architecture components include: a dedicated IT/OT DMZ (Level 3.5) containing the historian, data aggregation servers, and remote access jump hosts; unidirectional security gateways (data diodes) for historian synchronization from OT to IT, ensuring no return path exists; and application-layer firewalls with OT protocol deep packet inspection (Modbus, DNP3, IEC 61850) at Level 2/3 boundaries.

Remote access to OT must route exclusively through jump servers in the DMZ with mandatory multi-factor authentication, session recording, and just-in-time access provisioning. All vendor remote access must use dedicated, time-limited credentials rather than shared persistent accounts. Segmentation reduces blast radius: an IT-side ransomware infection or phishing compromise cannot directly reach PLC networks if the boundary controls are correctly configured. Regular penetration testing of IT/OT boundary controls, including attempts to pivot from historian to SCADA/HMI layers, validates segmentation effectiveness. Network diagrams must be kept current — undocumented connections are a persistent source of segmentation failures.
