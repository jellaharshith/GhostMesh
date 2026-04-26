---
id: mitre-t0836
source: MITRE ATT&CK for ICS T0836 Modify Parameter
tags: [mitre, ics, impact]
---
T0836 Modify Parameter describes adversaries altering process setpoints, alarm thresholds, control loop parameters, or safety system trip limits to cause out-of-specification operating conditions while evading detection. By raising alarm thresholds or modifying high/low limits, attackers can prevent automated alerting as process variables drift into dangerous ranges.

This technique is insidious because it operates within the normal command vocabulary of ICS systems — setpoint changes are a routine engineering activity. Adversaries who have studied process documentation can make parameter changes that are plausible enough to avoid immediate operator suspicion. For example, slightly raising the high-pressure alarm setpoint on a separator vessel by 5% — within the range an operator might adjust manually — could mask a gradual pressure increase toward a failure point.

Historical examples include the 2021 Oldsmar water treatment facility incident, where an attacker briefly raised sodium hydroxide setpoint to 111 times normal concentration. Defenses against T0836 include: immutable setpoint audit trails with cryptographic logging, alerting on setpoint changes outside of approved maintenance windows, requiring dual-person authorization for safety-critical parameter changes, and periodic automated comparison of live PLC setpoints against a known-good baseline stored in a protected configuration management database.
