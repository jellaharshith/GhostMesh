---
id: mitre-t0859
source: MITRE ATT&CK for ICS T0859 Valid Accounts
tags: [mitre, ics, lateral-movement, persistence]
---
T0859 Valid Accounts describes adversaries obtaining and using legitimate credentials to access ICS systems — achieving authentication bypass and making malicious activity blend with normal operations. In OT environments this technique is especially effective because ICS systems frequently lack the behavioral analytics to distinguish a legitimate operator from an adversary using stolen credentials.

VPN credentials are a primary target because they provide direct network access to OT segments from the internet. Service accounts used by historian software, data acquisition systems, and remote monitoring platforms often have broad permissions and are rarely monitored. Many ICS installations retain vendor default accounts or shared team credentials (e.g., "operator"/"operator123") that are documented in vendor manuals.

Volt Typhoon extensively used T0859 — obtaining VPN credentials through credential dumping and phishing to maintain persistent access to US critical infrastructure networks over years without deploying detectable malware. Detection is difficult and requires behavioral analytics: alerting on logins from unusual source IPs, off-hours authentication events, concurrent sessions from geographically disparate locations, and access to OT-sensitive systems by accounts not normally accessing them. Mandatory MFA on all remote access paths and aggressive credential rotation after any suspected compromise are the primary mitigations.
