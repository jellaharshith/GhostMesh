---
id: apt-volt-typhoon
source: CISA Advisory AA23-144A — Volt Typhoon
tags: [apt, china, ics, living-off-the-land, lateral-movement]
---
Volt Typhoon is a People's Republic of China state-sponsored cyber actor assessed by CISA, NSA, and Five Eyes partners to be pre-positioning for disruptive attacks against US critical infrastructure during a future geopolitical crisis, particularly a potential conflict over Taiwan. The group has been active since at least 2021, with intrusions confirmed in communications, energy, transportation, and water sector networks.

The defining characteristic of Volt Typhoon is an extreme reliance on living-off-the-land (LOTL) techniques — using built-in Windows tools (wmic, ntdsutil, netsh, certutil, PowerShell) and stolen legitimate credentials rather than custom malware. This approach minimizes the forensic footprint and defeats signature-based detection. The group uses legitimate VPN appliances with stolen credentials to maintain persistent access, conducts patient low-and-slow reconnaissance, and avoids any lateral movement activity that would generate anomalous network traffic volumes.

Volt Typhoon specifically avoids espionage-typical data exfiltration; the primary goal appears to be pre-positioning — establishing persistent, stealthy access paths that can be activated to disrupt or destroy critical infrastructure in a crisis scenario. Attribution confidence is high based on TTP overlap, infrastructure analysis, and human intelligence. Recommended mitigations include: hunting for LOLBin activity (wmic, nltest, net) on OT-adjacent systems, auditing VPN authentication logs for off-hours access, implementing phishing-resistant MFA, and patching internet-facing appliances within 24 hours of critical CVE disclosure.
