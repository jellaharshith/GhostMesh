---
id: mitre-t0830
source: MITRE ATT&CK for ICS T0830 Man in the Middle
tags: [mitre, ics, lateral-movement, collection]
---
T0830 Man in the Middle in ICS networks involves an adversary positioning themselves between a master station (SCADA/HMI) and field devices to intercept, observe, or manipulate process communications. Unlike IT MITM attacks focused on credential theft, ICS MITM often aims to inject false sensor readings or unauthorized control commands into real-time process streams.

OT protocols are highly vulnerable to MITM because most — Modbus TCP, DNP3, IEC 61850 GOOSE, EtherNet/IP — lack built-in authentication or encryption. An attacker with Layer 2 access can use ARP spoofing to redirect Modbus traffic between an HMI and a PLC, then forward legitimate traffic while selectively injecting crafted function codes (e.g., Write Single Coil FC05 to actuate a valve).

A particularly sophisticated application observed in Industroyer2 involves replaying captured legitimate IEC 104 ASDU sequences against substations to trip breakers while simultaneously sending false "normal" status back to the control room operator. This operator-blinding technique extends attack dwell time before physical effects are noticed. Defenses include deploying unidirectional gateways at ICS protocol boundaries, enabling DNP3 Secure Authentication v5, and monitoring for ARP anomalies on OT network segments.
