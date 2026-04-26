"""
Parser tests for deterministic keyword `parse_move` → dict, validated as ParsedMove.
"""
from __future__ import annotations

from backend.parser import parse_move
from backend.schemas import ParsedMove


def _pm(text: str) -> ParsedMove:
    return ParsedMove.model_validate(parse_move(text))


def test_isolate_explicit_asset():
    p = _pm("Isolate JH-01 from the OT network immediately")
    assert p.action == "isolate"
    assert p.actor == "Blue Team"
    assert "JH" in p.target.upper()
    assert p.confidence >= 0.5
    assert p.time_horizon == "immediate (< 1 hour)"


def test_patch_vpn():
    p = _pm("Patch CVE-2023-46805 on the VPN gateway before it's exploited")
    assert p.action == "patch"
    assert "VPN" in p.target.upper()
    assert p.technique_family == "vulnerability-management"


def test_scan_nmap():
    p = _pm("Run nmap against the OT network to enumerate open ports")
    assert p.action == "scan"
    assert p.technique_family == "active-reconnaissance"
    assert p.actor == "Blue Team"


def test_ambiguous_action_named_target():
    p = _pm("Do something about the historian")
    assert p.action == "unknown"
    assert "HIS" in p.target.upper() or p.target == "HISTORIAN"
    assert p.confidence <= 0.6


def test_empty_string():
    p = _pm("")
    assert p.action == "unknown"
    assert p.target == "unknown"


def test_monitor_wins_over_block_in_phrase_order():
    """First matching row in ACTION_MAP wins; 'monitor' appears before 'block' is checked in same string."""
    p = _pm("Monitor and block adversary traffic on FW-OT")
    assert p.action == "monitor"
    assert "FW" in p.target.upper() or p.target == "FIREWALL"
    assert 0.0 <= p.confidence <= 1.0


def test_restore_roundtrip_parsed_move():
    p = _pm("Restore JH-01 from backup immediately")
    p2 = ParsedMove.model_validate(p.model_dump())
    assert p2.action == "restore"
    assert p2.technique_family == "incident-recovery"
