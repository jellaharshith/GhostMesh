"""
LLM fallback for the hybrid parser using Anthropic.
Invoked only when deterministic confidence < 0.5.
Reads ANTHROPIC_API_KEY from env; missing key → returns None silently.
Uses tool_use for strict schema enforcement + prompt caching on system block.
"""
from __future__ import annotations

import hashlib
import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

# Load .env from ghostmesh root if present
_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    for _line in _env_path.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

_SYSTEM_PROMPT = (
    "You are a cyber-move parser for a wargaming engine. "
    "Parse the user's plain-English cyber action into structured JSON. "
    "Rules:\n"
    "- Never hallucinate. Use 'unknown' for any field you cannot confidently infer.\n"
    "- Prefer partial parse over wrong parse.\n"
    "- move_type: 'offensive' for attacker actions, 'defensive' for defender actions, "
    "'recon' for reconnaissance, 'unknown' if unclear.\n"
    "- actor: 'Blue Team' for defender, 'Red Team' for attacker, 'unknown' if unclear.\n"
    "- stealth_level: 'low' | 'medium' | 'high'\n"
    "- risk: 'low' | 'medium' | 'high'\n"
    "- confidence: float 0.0-1.0 reflecting YOUR confidence in the parse.\n"
    "- unknowns: list of field names you could not resolve.\n"
    "- assumptions: list of assumptions you made.\n"
    "- mitre_attack_id: MITRE ATT&CK technique ID (e.g. 'T1190') or null.\n"
    "Return only via the provided tool schema."
)

_TOOL_SCHEMA = {
    "name": "structured_parse",
    "description": "Return the structured cyber-move parse.",
    "input_schema": {
        "type": "object",
        "properties": {
            "actor": {"type": "string", "enum": ["Blue Team", "Red Team", "unknown"]},
            "move_type": {"type": "string", "enum": ["offensive", "defensive", "recon", "unknown"]},
            "action": {"type": "string"},
            "target": {"type": "string"},
            "intent": {"type": "string"},
            "technique_family": {"type": "string"},
            "mitre_attack_id": {"type": ["string", "null"]},
            "stealth_level": {"type": "string", "enum": ["low", "medium", "high"]},
            "risk": {"type": "string", "enum": ["low", "medium", "high"]},
            "time_horizon": {"type": "string"},
            "assumptions": {"type": "array", "items": {"type": "string"}},
            "unknowns": {"type": "array", "items": {"type": "string"}},
            "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        },
        "required": [
            "actor", "move_type", "action", "target", "intent",
            "technique_family", "stealth_level", "risk", "time_horizon",
            "assumptions", "unknowns", "confidence",
        ],
    },
}


@lru_cache(maxsize=256)
def _cached_llm_parse(text_hash: str, text: str) -> Optional[str]:
    """Returns raw JSON string or None. Cached by text hash."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    try:
        import anthropic  # lazy import
    except ImportError:
        return None

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            system=[
                {
                    "type": "text",
                    "text": _SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            tools=[_TOOL_SCHEMA],
            tool_choice={"type": "tool", "name": "structured_parse"},
            messages=[{"role": "user", "content": text}],
        )
        for block in response.content:
            if block.type == "tool_use" and block.name == "structured_parse":
                return json.dumps(block.input)
    except Exception:
        return None

    return None


def parse_with_llm(text: str) -> Optional[Dict[str, Any]]:
    """Returns parsed dict or None on any failure / missing key."""
    text_hash = hashlib.sha256(text.encode()).hexdigest()
    raw = _cached_llm_parse(text_hash, text)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None
