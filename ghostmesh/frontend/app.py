"""GhostMesh — Streamlit frontend (command-center edition)"""
from __future__ import annotations
import json
import re
from typing import Any, Dict, List, Optional

import requests
import streamlit as st

# ── Config ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GhostMesh",
    page_icon="🕸️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Theme CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ════════════════════════════════════════════
   GHOSTMESH · COMMAND-CENTER UI
   Design tokens
   ════════════════════════════════════════════
   --bg-base:      #0d0f12   (app background)
   --bg-card:      #111620   (card surface)
   --bg-elevated:  #0f1419   (mission header)
   --bg-inset:     #0a0e14   (inputs, inset blocks)
   --border:       #1e2a38   (standard border)
   --border-dim:   #161c24   (row dividers)
   --accent:       #b03030   (brand red)
   --text-primary: #d4dbe6   (headings)
   --text-body:    #8a97a8   (body copy)
   --text-dim:     #5a6a7a   (labels, muted)
   --text-faint:   #3a4a5a   (section caps)
   --blue-value:   #7aafd4   (value pills)
   ════════════════════════════════════════════ */

/* ── Reset & base ─────────────────────────── */
*, *::before, *::after { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"] {
    background-color: #0d0f12 !important;
    color: #d4dbe6 !important;
    font-family: 'Inter', 'SF Pro Text', 'Segoe UI', system-ui, sans-serif;
    font-size: 14px;
    -webkit-font-smoothing: antialiased;
}

/* Tighten Streamlit's default page padding for 1366px screens */
[data-testid="stAppViewContainer"] > .main > .block-container {
    padding: 1.5rem 1.75rem 2rem !important;
    max-width: 1320px !important;
}

[data-testid="stSidebar"] {
    background-color: #0e1218 !important;
    border-right: 1px solid #1a2230 !important;
}

[data-testid="stSidebar"] > div:first-child {
    padding: 1rem 0.9rem !important;
}

/* ── Tabs ──────────────────────────────────── */
[data-testid="stTabs"] button {
    font-size: 0.68rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: #3e4e60 !important;
    border-bottom: 2px solid transparent !important;
    padding: 7px 16px 6px !important;
    transition: color 0.15s ease !important;
}

[data-testid="stTabs"] button[aria-selected="true"] {
    color: #d4dbe6 !important;
    border-bottom: 2px solid #b03030 !important;
    background: none !important;
}

[data-testid="stTabs"] button:hover:not([aria-selected="true"]) {
    color: #7a8a9a !important;
}

[data-testid="stTabs"] [role="tablist"] {
    border-bottom: 1px solid #1a2230 !important;
    gap: 0 !important;
    margin-bottom: 1.25rem !important;
}

/* ── Cards ──────────────────────────────────── */
.gm-card {
    background: #111620;
    border: 1px solid #1e2a38;
    border-radius: 5px;
    padding: 14px 16px 16px;
    margin-bottom: 10px;
    /* stretch cards to equal height inside a flex column */
    display: flex;
    flex-direction: column;
}

.gm-card-header {
    font-size: 0.6rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #3e4e60;
    margin-bottom: 10px;
    padding-bottom: 7px;
    border-bottom: 1px solid #1a2230;
    flex-shrink: 0;
}

.gm-card-body {
    flex: 1;
}

.gm-body {
    font-size: 0.83rem;
    color: #8a97a8;
    line-height: 1.6;
}

/* ── Mission header banner ──────────────────── */
.gm-mission-header {
    background: #0f1419;
    border: 1px solid #1e2a38;
    border-left: 3px solid #b03030;
    border-radius: 5px;
    padding: 13px 18px;
    margin-bottom: 14px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 10px;
}

.gm-mission-eyebrow {
    font-size: 0.56rem;
    font-weight: 700;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: #3a4a5a;
    margin-bottom: 4px;
}

.gm-mission-title {
    font-size: 1rem;
    font-weight: 700;
    letter-spacing: 0.01em;
    color: #d4dbe6;
    line-height: 1.3;
}

.gm-mission-meta {
    display: flex;
    align-items: center;
    gap: 14px;
    flex-wrap: wrap;
}

.gm-mission-metric {
    text-align: center;
    flex-shrink: 0;
}

.gm-mission-metric-label {
    display: block;
    font-size: 0.52rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #3a4a5a;
    margin-bottom: 3px;
}

/* ── Status chips / badges ──────────────────── */
.chip {
    display: inline-block;
    font-size: 0.56rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 3px 7px 2px;
    border-radius: 2px;
    white-space: nowrap;
    line-height: 1.4;
}
.chip-red    { background: #321010; color: #e05050; border: 1px solid #5a1a1a; }
.chip-amber  { background: #271c00; color: #c88020; border: 1px solid #503800; }
.chip-green  { background: #091a12; color: #2ea87e; border: 1px solid #104530; }
.chip-slate  { background: #101826; color: #5a7a9a; border: 1px solid #1c2e40; }
.chip-white  { background: #171e2c; color: #7a8a9e; border: 1px solid #242e40; }

/* ── Table ──────────────────────────────────── */
.gm-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.79rem;
    table-layout: fixed;
}
.gm-table colgroup col:nth-child(1) { width: 28%; }
.gm-table colgroup col:nth-child(2) { width: 30%; }
.gm-table colgroup col:nth-child(3) { width: 22%; }
.gm-table colgroup col:nth-child(4) { width: 20%; }

.gm-table th {
    font-size: 0.58rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #3e4e60;
    padding: 7px 10px 6px;
    border-bottom: 1px solid #1e2a38;
    text-align: left;
    white-space: nowrap;
}
.gm-table td {
    padding: 8px 10px;
    border-bottom: 1px solid #141c26;
    color: #8a97a8;
    vertical-align: middle;
    word-break: break-word;
    line-height: 1.45;
}
.gm-table tr:last-child td { border-bottom: none; }
.gm-table tr:hover td { background: #131a24; }
.gm-table td:first-child { color: #b8c4d4; font-weight: 600; }

/* ── Key-value rows ─────────────────────────── */
.gm-kv-row {
    display: flex;
    align-items: flex-start;
    padding: 6px 0 5px;
    border-bottom: 1px solid #141c26;
    gap: 10px;
    min-height: 30px;
}
.gm-kv-row:last-child { border-bottom: none; }

.gm-kv-key {
    min-width: 136px;
    max-width: 136px;
    color: #4e5e70;
    font-size: 0.67rem;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    padding-top: 2px;
    flex-shrink: 0;
    line-height: 1.4;
}
.gm-kv-val {
    color: #9aa8b8;
    font-size: 0.81rem;
    line-height: 1.5;
    word-break: break-word;
    flex: 1;
}

/* ── Sub-section divider inside a card ─────── */
.gm-sub-header {
    font-size: 0.56rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #3a4a5a;
    padding: 9px 0 5px;
    border-bottom: 1px solid #1a2230;
    margin-bottom: 2px;
}

/* ── Bullet list ────────────────────────────── */
.gm-bullet-list {
    list-style: none;
    margin: 0;
    padding: 0;
}
.gm-bullet-list li {
    padding: 4px 0 3px;
    border-bottom: 1px solid #141c26;
    font-size: 0.8rem;
    color: #8a97a8;
    line-height: 1.55;
    padding-left: 14px;
    position: relative;
}
.gm-bullet-list li:last-child { border-bottom: none; }
.gm-bullet-list li::before {
    content: "▸";
    color: #384858;
    position: absolute;
    left: 0;
    top: 4px;
    font-size: 0.65rem;
}

/* ── Value pill ─────────────────────────────── */
.gm-value {
    display: inline-block;
    background: #0c1420;
    color: #7aafd4;
    font-size: 0.77rem;
    padding: 2px 8px 1px;
    border-radius: 3px;
    border: 1px solid #1c2e40;
    font-weight: 500;
    white-space: nowrap;
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* ── Section label (page-level) ─────────────── */
.gm-section-label {
    font-size: 0.58rem;
    font-weight: 700;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: #3a4a5a;
    margin-bottom: 8px;
    margin-top: 2px;
}

/* ── Metric row (legacy, kept for compat) ───── */
.gm-metric-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 5px 0;
    border-bottom: 1px solid #141c26;
    font-size: 0.78rem;
}
.gm-metric-label { color: #5a6a7a; font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.07em; }
.gm-metric-value { font-weight: 700; font-size: 0.82rem; }

/* ── Sidebar ────────────────────────────────── */
[data-testid="stSidebar"] .stTextInput input,
[data-testid="stSidebar"] .stSelectbox select,
[data-testid="stSidebar"] .stTextArea textarea {
    background: #0a0e14 !important;
    border: 1px solid #1e2a38 !important;
    color: #8a97a8 !important;
    font-size: 0.78rem !important;
    border-radius: 3px !important;
}

[data-testid="stSidebar"] label {
    font-size: 0.64rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: #3e4e60 !important;
}

/* ── Buttons ────────────────────────────────── */
[data-testid="stButton"] button[kind="primary"] {
    background: #5a1a1a !important;
    color: #f0d0d0 !important;
    border: 1px solid #a02828 !important;
    border-radius: 3px !important;
    font-size: 0.7rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.09em !important;
    text-transform: uppercase !important;
    padding: 0.45rem 1rem !important;
    transition: background 0.15s ease !important;
}
[data-testid="stButton"] button[kind="primary"]:hover {
    background: #6e2020 !important;
}

[data-testid="stButton"] button[kind="secondary"],
[data-testid="stButton"] button:not([kind]) {
    background: #111620 !important;
    color: #7a8a9a !important;
    border: 1px solid #1e2a38 !important;
    border-radius: 3px !important;
    font-size: 0.68rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.07em !important;
    text-transform: uppercase !important;
    padding: 0.42rem 0.9rem !important;
}

/* ── Expanders ──────────────────────────────── */
[data-testid="stExpander"] {
    background: #0e1420 !important;
    border: 1px solid #1e2a38 !important;
    border-radius: 4px !important;
    margin-top: 6px !important;
}
[data-testid="stExpander"] summary {
    font-size: 0.68rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.07em !important;
    color: #5a6a7a !important;
    padding: 8px 12px !important;
}
[data-testid="stExpander"] > div[data-testid="stExpanderDetails"] {
    padding: 4px 12px 10px !important;
}

/* ── Alerts ─────────────────────────────────── */
[data-testid="stAlert"] {
    font-size: 0.78rem !important;
    border-radius: 3px !important;
    padding: 8px 12px !important;
}

/* ── Streamlit chrome cleanup ───────────────── */
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stDecoration"] { display: none !important; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }

/* ── Text area ──────────────────────────────── */
.stTextArea textarea {
    background: #0a0e14 !important;
    border: 1px solid #1e2a38 !important;
    color: #8a97a8 !important;
    font-size: 0.82rem !important;
    border-radius: 3px !important;
    line-height: 1.6 !important;
}

/* ── Divider ────────────────────────────────── */
hr { border-color: #1a2230 !important; opacity: 1 !important; margin: 0.6rem 0 !important; }

/* ── Progress bar ───────────────────────────── */
[data-testid="stProgressBar"] > div > div { background: #b03030 !important; }

/* ── Sidebar wordmark ───────────────────────── */
.gm-wordmark {
    font-size: 0.82rem;
    font-weight: 800;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #bbc4d0;
}
.gm-wordmark-sub {
    font-size: 0.56rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #3a4a5a;
    margin-top: 2px;
}

/* ── Column containers ──────────────────────── */
[data-testid="column"] { padding: 0 5px !important; }

/* ── Confidence / parser warning note ──────── */
.gm-confidence-note {
    background: #181200;
    border: 1px solid #483000;
    border-left: 3px solid #b87820;
    border-radius: 3px;
    padding: 9px 13px;
    font-size: 0.76rem;
    color: #987020;
    margin-top: 10px;
    line-height: 1.55;
}

/* ── Dim note (empty state inside cards) ───── */
.gm-dim-note {
    color: #3a4a5a;
    font-size: 0.74rem;
    font-style: italic;
}

/* ── Inline collapsible (used inside timeline expanders) ── */
details.gm-details {
    margin-top: 6px;
    border: 1px solid #1e2a38;
    border-radius: 3px;
    background: #0e1420;
}
details.gm-details summary {
    cursor: pointer;
    padding: 6px 10px;
    font-size: 0.67rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #4e5e70;
    list-style: none;
    user-select: none;
}
details.gm-details summary::-webkit-details-marker { display: none; }
details.gm-details summary::before {
    content: "▸ ";
    color: #3a4a5a;
    font-size: 0.6rem;
}
details.gm-details[open] summary::before { content: "▾ "; }
details.gm-details .gm-details-body {
    padding: 6px 12px 10px;
    border-top: 1px solid #1a2230;
}

/* ── Debug banner ───────────────────────────── */
.gm-debug-banner {
    background: #180a00;
    border: 1px solid #503000;
    border-radius: 3px;
    padding: 5px 10px;
    font-size: 0.62rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #b07020;
    margin-bottom: 8px;
}

/* ── Responsive: 1366px & narrower ─────────── */
@media screen and (max-width: 1400px) {
    [data-testid="stAppViewContainer"] > .main > .block-container {
        padding: 1.25rem 1.25rem 2rem !important;
    }
    .gm-kv-key { min-width: 118px; max-width: 118px; }
    .gm-table { font-size: 0.75rem; }
    .gm-table td, .gm-table th { padding: 6px 8px; }
    .gm-mission-title { font-size: 0.92rem; }
    [data-testid="column"] { padding: 0 3px !important; }
}
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "last_result" not in st.session_state:
    st.session_state["last_result"] = None
if "active_scenario_id" not in st.session_state:
    st.session_state["active_scenario_id"] = None
if "debug_mode" not in st.session_state:
    st.session_state["debug_mode"] = False

# ── Constants ─────────────────────────────────────────────────────────────────
STATUS_CHIP = {
    "at-risk":          '<span class="chip chip-amber">AT-RISK</span>',
    "compromised":      '<span class="chip chip-red">COMPROMISED</span>',
    "clean":            '<span class="chip chip-green">CLEAN</span>',
    "online":           '<span class="chip chip-green">ONLINE</span>',
    "patching-pending": '<span class="chip chip-amber">PATCHING</span>',
    "defaced":          '<span class="chip chip-red">DEFACED</span>',
}
SEVERITY_CHIP = {
    "high": '<span class="chip chip-red">HIGH</span>',
    "med":  '<span class="chip chip-amber">MED</span>',
    "low":  '<span class="chip chip-green">LOW</span>',
}
ESCALATION_CHIP = {
    "retreat":              '<span class="chip chip-green">RETREAT</span>',
    "hold":                 '<span class="chip chip-amber">HOLD</span>',
    "escalate":             '<span class="chip chip-amber">ESCALATE</span>',
    "escalate_destructive": '<span class="chip chip-red">ESCALATE — DESTRUCTIVE</span>',
}
HORIZON_LABEL = {
    "immediate":   "⚡ Immediate",
    "next-turn":   "⏱ Next Turn",
    "medium-term": "📅 Medium Term",
}
ASSET_FUNCTION_MAP = {
    "scada":        "Industrial Control",
    "hmi":          "Human-Machine Interface",
    "firewall":     "Perimeter Defense",
    "dns":          "Name Resolution",
    "vpn":          "Remote Access",
    "database":     "Data Storage",
    "web":          "Web Services",
    "email":        "Communications",
    "auth":         "Authentication",
    "monitoring":   "Threat Monitoring",
}

# Human-readable label overrides for raw field names
FIELD_LABELS: Dict[str, str] = {
    "action":               "Action",
    "target":               "Target",
    "actor":                "Actor",
    "intent":               "Intent",
    "technique_family":     "Technique Family",
    "stealth_level":        "Stealth Level",
    "risk":                 "Risk Level",
    "time_horizon":         "Time Horizon",
    "confidence":           "Parser Confidence",
    "success_probability":  "Success Probability",
    "detection_risk":       "Detection Risk",
    "attribution_risk":     "Attribution Risk",
    "red_action":           "Red Team Action",
    "cascading_effects":    "Follow-on Effects",
    "rationale":            "Assessment",
    "assumptions":          "Analyst Assumptions",
    "escalation_level":     "Escalation Level",
    "effects":              "Operational Effects",
}

# ── Formatter utilities ───────────────────────────────────────────────────────

def _na(v: Any, default: str = "Not available") -> str:
    """
    Return a safe display string.
    - None / empty → default
    - Dict / list   → placeholder (never Python repr in the UI)
    - "unknown" etc → "Needs analyst review"
    """
    if v is None:
        return default
    if isinstance(v, (dict, list)):
        # Structured objects should never appear as raw strings in the UI
        return "See detailed view"
    s = str(v).strip()
    if not s:
        return default
    if s.lower() in ("none", "null", "undefined", "unknown", "n/a", "na"):
        return "Needs analyst review"
    return s


def _safe_float(v: Any, default: float = 0.0) -> float:
    """Safely coerce any value to float, returning default on failure."""
    if v is None:
        return default
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _field_label(key: str) -> str:
    return FIELD_LABELS.get(key, key.replace("_", " ").title())


def _pct(v: Any) -> str:
    return f"{_safe_float(v) * 100:.0f}%"


def _risk_chip(v: Any) -> str:
    f = _safe_float(v)
    if f >= 0.66:
        return f'<span class="chip chip-red">{_pct(f)}</span>'
    if f >= 0.33:
        return f'<span class="chip chip-amber">{_pct(f)}</span>'
    return f'<span class="chip chip-green">{_pct(f)}</span>'


def _success_chip(v: Any) -> str:
    f = _safe_float(v)
    if f >= 0.66:
        return f'<span class="chip chip-green">{_pct(f)}</span>'
    if f >= 0.33:
        return f'<span class="chip chip-amber">{_pct(f)}</span>'
    return f'<span class="chip chip-red">{_pct(f)}</span>'


def _escalation_chip(esc: Any) -> str:
    if not esc or not isinstance(esc, str):
        return '<span class="chip chip-white">Pending</span>'
    chip = ESCALATION_CHIP.get(esc.lower().strip())
    if chip:
        return chip
    # Humanize the raw value rather than show it directly
    label = esc.replace("_", " ").title()
    return f'<span class="chip chip-white">{label}</span>'


def _asset_function(asset: Dict) -> str:
    atype = (asset.get("type") or "").lower()
    for k, v in ASSET_FUNCTION_MAP.items():
        if k in atype:
            return v
    raw = asset.get("type")
    return _na(raw, "—").title() if raw else "—"


def _asset_risk(asset: Dict) -> str:
    status = (asset.get("status") or "online").lower()
    if status in ("compromised", "defaced"):
        return '<span class="chip chip-red">CRITICAL</span>'
    if status in ("at-risk", "patching-pending"):
        return '<span class="chip chip-amber">ELEVATED</span>'
    return '<span class="chip chip-green">NOMINAL</span>'


def _clean_effect(e: Any) -> str:
    """
    Convert any effect item to a clean readable string.
    - Strips bracket prefixes like [T2] or [immediate]
    - Handles dict objects by extracting description
    - Never returns Python repr
    """
    if isinstance(e, dict):
        desc = e.get("description") or e.get("text") or e.get("effect") or ""
        s = str(desc).strip()
        return s if s else "Effect details not available"
    if isinstance(e, str):
        cleaned = e.split("] ", 1)[-1] if "] " in e else e
        return cleaned.strip() or "Effect details not available"
    # Lists or other types — flatten to nothing visible
    return "Effect details not available"


def _strip_markdown(text: str) -> str:
    """
    Strip common LLM markdown artifacts so they never appear in rendered HTML.
    Handles: fenced code blocks, inline code, headers, bold, italic, bullets.
    Does NOT touch plain prose — safe to run on all AAR text.
    """
    # Remove fenced code blocks (```...```)
    text = re.sub(r"```[\s\S]*?```", "[code block removed]", text)
    # Remove inline code (`...`)
    text = re.sub(r"`[^`\n]+`", lambda m: m.group(0)[1:-1], text)
    # Convert ## headers to plain text (remove # markers)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    # Remove bold/italic markers (**text**, *text*, __text__, _text_)
    text = re.sub(r"\*{1,2}([^*\n]+)\*{1,2}", r"\1", text)
    text = re.sub(r"_{1,2}([^_\n]+)_{1,2}", r"\1", text)
    # Convert markdown bullets (- item, * item) to plain text
    text = re.sub(r"^[\*\-]\s+", "• ", text, flags=re.MULTILINE)
    # Strip trailing whitespace per line
    text = "\n".join(line.rstrip() for line in text.splitlines())
    return text.strip()


def _value_pill(text: str) -> str:
    """Render a value as a styled pill — never raw code."""
    return f'<span class="gm-value">{_na(text)}</span>'


def _kv_row(label: str, value_html: str) -> str:
    return f'<div class="gm-kv-row"><span class="gm-kv-key">{label}</span><span class="gm-kv-val">{value_html}</span></div>'


def _section_divider(label: str) -> str:
    return f'<div class="gm-sub-header">{label}</div>'


def _bullet_list(items: List[str], pre_rendered: bool = False) -> str:
    """
    Render a list as styled bullets.
    - pre_rendered=True: items already contain safe HTML (chips etc.), skip _na()
    - pre_rendered=False (default): items are plain strings, sanitize each
    """
    filtered = [i for i in items if i and str(i).strip()]
    if not filtered:
        return '<span class="gm-dim-note">None noted.</span>'
    if pre_rendered:
        li = "".join(f"<li>{i}</li>" for i in filtered)
    else:
        li = "".join(f"<li>{_na(i)}</li>" for i in filtered)
    return f'<ul class="gm-bullet-list">{li}</ul>'


# ── Presentation-layer formatters ─────────────────────────────────────────────

def format_parsed_move(p: Dict) -> str:
    """Render parsed move fields as a clean key-value block."""
    confidence = _safe_float(p.get("confidence"))
    low_confidence = confidence < 0.5

    action_raw  = _na(p.get("action"))
    target_raw  = _na(p.get("target"))
    intent_raw  = _na(p.get("intent"))
    tech_raw    = _na(p.get("technique_family"))
    stealth_raw = _na(p.get("stealth_level"))
    risk_raw    = _na(p.get("risk"))
    horizon_raw = p.get("time_horizon", "")
    horizon_label = HORIZON_LABEL.get(horizon_raw, _na(horizon_raw))

    rows = (
        _kv_row("Actor",            _value_pill(_na(p.get("actor", "Blue Team"))))
        + _kv_row("Action",         _value_pill(action_raw))
        + _kv_row("Target",         _value_pill(target_raw))
        + _kv_row("Intent",           f'<span class="gm-body">{intent_raw}</span>')
        + _kv_row("Technique Family", _value_pill(tech_raw))
        + _kv_row("Stealth Level",    _value_pill(stealth_raw))
        + _kv_row("Risk Level",       _value_pill(risk_raw))
        + _kv_row("Time Horizon",     f'<span class="gm-body">{horizon_label}</span>')
        + _kv_row("Parser Confidence", _success_chip(confidence))
    )

    confidence_note = ""
    if low_confidence:
        confidence_note = """
        <div class="gm-confidence-note">
            Parser confidence is limited on this move.<br>
            Analyst review is recommended before execution.
        </div>"""

    return rows + confidence_note


def format_result_move_summary(p: Dict, adj: Dict, red: Dict) -> Dict[str, str]:
    """Top banner data for the Result tab."""
    esc = red.get("escalation_level") or ""
    return {
        "action":       _na(p.get("action")),
        "target":       _na(p.get("target")),
        "success_chip": _success_chip(_safe_float(adj.get("success_probability"))),
        "detect_chip":  _risk_chip(_safe_float(adj.get("detection_risk"))),
        "attr_chip":    _risk_chip(_safe_float(adj.get("attribution_risk"))),
        "esc_chip":     _escalation_chip(esc),
    }


def format_adjudication(adj: Dict) -> str:
    """Render adjudication fields as human-readable HTML."""
    sp = _safe_float(adj.get("success_probability"))
    dr = _safe_float(adj.get("detection_risk"))
    ar = _safe_float(adj.get("attribution_risk"))

    metrics = (
        _kv_row("Success Probability", _success_chip(sp))
        + _kv_row("Detection Risk",    _risk_chip(dr))
        + _kv_row("Attribution Risk",  _risk_chip(ar))
    )

    effects = adj.get("effects") or []
    effect_strs = [_clean_effect(e) for e in effects if e]
    effects_html = _section_divider("Operational Effects") + _bullet_list(effect_strs)

    cascading = adj.get("cascading_effects") or []
    cascade_items = []
    for ce in cascading:
        if isinstance(ce, dict):
            h = ce.get("horizon") or "medium-term"
            s = (ce.get("severity") or "low").lower()
            d = _na(ce.get("description"), "")
            if not d or d == "Not available":
                continue
            sev_chip = SEVERITY_CHIP.get(s, '<span class="chip chip-white">—</span>')
            horizon_label = HORIZON_LABEL.get(h, h.replace("-", " ").title())
            cascade_items.append(f'{horizon_label} &nbsp;{sev_chip}&nbsp; {d}')
        elif ce:
            cleaned = _clean_effect(ce)
            if cleaned and cleaned != "Effect details not available":
                cascade_items.append(cleaned)

    # cascade_items contain HTML chips — use pre_rendered=True
    cascade_html = (
        _section_divider("Follow-on Effects") + _bullet_list(cascade_items, pre_rendered=True)
        if cascade_items else ""
    )

    return metrics + effects_html + cascade_html


def format_red_response(red: Dict) -> str:
    esc = red.get("escalation_level", "")
    return (
        _kv_row("Escalation Level", _escalation_chip(esc))
        + _kv_row("Target",         _value_pill(_na(red.get("target"))))
        + _section_divider("Red Team Action")
        + f'<div class="gm-body" style="margin-bottom:6px">{_na(red.get("red_action"))}</div>'
        + _section_divider("Red Team Intent")
        + f'<div class="gm-body">{_na(red.get("intent"))}</div>'
    )


def format_aar(aar: Dict) -> str:
    """
    Render AAR as a structured executive debrief.
    Strips markdown artifacts so the output is always plain prose.
    """
    if not aar or not isinstance(aar, dict):
        return ""
    ui_text = aar.get("ui_text") or ""
    if not isinstance(ui_text, str):
        return ""
    return _strip_markdown(ui_text)


def format_timeline_entry(turn: Dict) -> Dict[str, Any]:
    """Extract display fields for a timeline card."""
    p   = turn.get("parsed") or {}
    adj = turn.get("adjudication") or {}
    red = turn.get("red") or {}
    esc = red.get("escalation_level") or ""
    sp  = _safe_float(adj.get("success_probability"))

    effects   = adj.get("effects") or []
    cascading = adj.get("cascading_effects") or []
    all_effects: List[str] = []
    for e in effects:
        c = _clean_effect(e)
        if c and c != "Effect details not available":
            all_effects.append(c)
    for ce in cascading:
        if isinstance(ce, dict):
            d = _na(ce.get("description"), "")
            if d and d != "Not available":
                all_effects.append(d)
        elif ce:
            c = _clean_effect(ce)
            if c and c != "Effect details not available":
                all_effects.append(c)

    action_raw = _na(p.get("action"))
    target_raw = _na(p.get("target"))

    # Build a clean label fallback if parser returned placeholder text
    action_label = action_raw if len(action_raw) < 40 else action_raw[:38] + "…"
    target_label = target_raw if len(target_raw) < 30 else target_raw[:28] + "…"

    return {
        "turn_id":       str(turn.get("turn_id") or "—"),
        "blue_move":     _na(turn.get("blue_move")),
        "action":        action_raw,
        "action_label":  action_label,
        "target":        target_raw,
        "target_label":  target_label,
        "outcome_chip":  _success_chip(sp),
        "success_pct":   _pct(sp),
        "detection_chip":_risk_chip(_safe_float(adj.get("detection_risk"))),
        "esc_chip":      _escalation_chip(esc),
        "red_action":    _na(red.get("red_action")),
        "effects_list":  all_effects,
        "rationale":     _na(adj.get("rationale")),
        "red_rationale": _na(red.get("rationale")),
    }


# ── Shared UI primitives ──────────────────────────────────────────────────────

def _inline_collapsible(summary: str, body_html: str) -> str:
    """
    HTML <details> element — safe to use inside st.expander (no Streamlit nesting).
    Returns an HTML string to be included in a larger markdown block.
    """
    return f"""<details class="gm-details">
  <summary>{summary}</summary>
  <div class="gm-details-body gm-body">{body_html}</div>
</details>"""


def _card(header: str, body_html: str) -> None:
    st.markdown(f"""
    <div class="gm-card">
        <div class="gm-card-header">{header}</div>
        <div class="gm-card-body">{body_html}</div>
    </div>
    """, unsafe_allow_html=True)


def _debug_json(label: str, data: Any) -> None:
    """Show raw JSON only in debug mode."""
    if st.session_state.get("debug_mode"):
        with st.expander(f"[DEV] {label}"):
            st.json(data)


# ── HTTP helpers ──────────────────────────────────────────────────────────────

def _get(path: str, api_url: str) -> Optional[Any]:
    try:
        r = requests.get(f"{api_url}{path}", timeout=8)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error(f"Cannot reach API at {api_url}. Is the backend running?")
        return None
    except Exception as e:
        st.error(f"API error: {e}")
        return None


def _post(path: str, payload: Dict[str, Any], api_url: str) -> Optional[Any]:
    try:
        r = requests.post(f"{api_url}{path}", json=payload, timeout=15)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error(f"Cannot reach API at {api_url}.")
        return None
    except requests.exceptions.HTTPError as e:
        detail = r.json().get("detail", str(e)) if r.content else str(e)
        st.error(f"API error: {detail}")
        return None
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return None


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:8px 0 12px 0">
        <div class="gm-wordmark">GhostMesh</div>
        <div class="gm-wordmark-sub">AI Cyber Wargaming Engine</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<hr style="margin:0 0 12px 0">', unsafe_allow_html=True)

    api_url = "http://localhost:8029"
    st.markdown('<hr style="margin:8px 0">', unsafe_allow_html=True)

    st.markdown('<div class="gm-section-label">Scenario</div>', unsafe_allow_html=True)
    scenarios_list: List[Dict] = _get("/scenarios", api_url) or []
    scenario_names = [s["name"] for s in scenarios_list]
    scenario_ids   = [s["id"]   for s in scenarios_list]

    current_idx = 0
    if st.session_state["active_scenario_id"] in scenario_ids:
        current_idx = scenario_ids.index(st.session_state["active_scenario_id"])

    if scenarios_list:
        # Build display labels — append (id suffix) when names collide to avoid mis-selection
        name_counts: Dict[str, int] = {}
        for n in scenario_names:
            name_counts[n] = name_counts.get(n, 0) + 1
        display_labels = [
            f"{s['name']} [{s['id'][-6:]}]" if name_counts[s["name"]] > 1 else s["name"]
            for s in scenarios_list
        ]
        id_to_label = {s["id"]: lbl for s, lbl in zip(scenarios_list, display_labels)}
        chosen_id = st.selectbox(
            "Select scenario",
            options=scenario_ids,
            format_func=lambda sid: id_to_label.get(sid, sid),
            index=current_idx,
            label_visibility="collapsed",
        )
        if chosen_id != st.session_state.get("active_scenario_id"):
            res = _post("/scenarios/select", {"scenario_id": chosen_id}, api_url)
            if res:
                st.session_state["active_scenario_id"] = chosen_id
                st.rerun()

    st.markdown('<div class="gm-section-label" style="margin-top:10px">New Scenario</div>', unsafe_allow_html=True)
    scenario_query = st.text_input(
        "Scenario",
        placeholder="e.g. Volt Typhoon Texas power grid",
        key="scenario_input",
        label_visibility="collapsed",
    )
    st.caption("GDELT · ACLED · UCDP · OSM · JP 3-12 doctrine")
    if st.button("⚡ Launch Scenario", use_container_width=True, type="primary"):
        if scenario_query.strip():
            with st.spinner("Fusing live intelligence…"):
                seeded = _post("/scenarios/seed", {"query": scenario_query.strip(), "use_api": True, "use_acled": True}, api_url)
            if seeded:
                sources = " · ".join(s.upper() for s in seeded.get("sources_used", [])) or "SEED"
                st.success(f"✓ {sources} — **{seeded['name']}**")
                st.session_state["active_scenario_id"] = seeded.get("id", "")
                st.rerun()
        else:
            st.warning("Enter a scenario query first.")

    st.markdown('<hr style="margin:8px 0">', unsafe_allow_html=True)
    if st.button("Reset Session", use_container_width=True):
        r = _post("/reset", {}, api_url)
        if r:
            st.session_state["last_result"] = None
            st.success("Session cleared.")
            st.rerun()

    # ── Developer debug toggle (off by default) ──
    st.markdown('<hr style="margin:8px 0">', unsafe_allow_html=True)
    with st.expander("Developer Options"):
        debug_on = st.toggle(
            "Debug mode (show raw JSON)",
            value=st.session_state["debug_mode"],
            key="debug_toggle",
        )
        st.session_state["debug_mode"] = debug_on
        if debug_on:
            st.markdown('<div class="gm-debug-banner">⚠ Debug mode active — raw JSON visible</div>', unsafe_allow_html=True)

    st.markdown('<div style="padding-top:8px"><span style="font-size:0.6rem;letter-spacing:0.1em;text-transform:uppercase;color:#2e3a4a">Blue Team Interface · Plain English Only</span></div>', unsafe_allow_html=True)


# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_brief, tab_move, tab_result, tab_aar, tab_timeline = st.tabs([
    "BRIEF", "MOVE", "RESULT", "AAR", "TIMELINE"
])


# ── Tab 1: Brief ──────────────────────────────────────────────────────────────
with tab_brief:
    scenario = _get("/scenario", api_url)
    if not scenario:
        st.markdown('<div class="gm-body" style="padding:20px 0">No active scenario. Select or load one from the sidebar.</div>', unsafe_allow_html=True)
    else:
        tension = scenario.get("tension_level", 0.5)
        if tension >= 0.7:
            threat_chip = '<span class="chip chip-red">CRITICAL</span>'
        elif tension >= 0.45:
            threat_chip = '<span class="chip chip-amber">ELEVATED</span>'
        else:
            threat_chip = '<span class="chip chip-green">NOMINAL</span>'

        # Mission header
        st.markdown(f"""
        <div class="gm-mission-header">
            <div>
                <div class="gm-mission-eyebrow">Mission Brief</div>
                <div class="gm-mission-title">{_na(scenario.get('name'))}</div>
            </div>
            <div class="gm-mission-metric">
                <span class="gm-mission-metric-label">Threat Level</span>
                {threat_chip}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Situation summary
        brief_text = _na(scenario.get("brief"), "No brief available.")
        _card("Scenario Summary", f'<div class="gm-body">{brief_text}</div>')

        # Two-column: objectives + red posture
        col_l, col_r = st.columns(2)

        with col_l:
            objs = scenario.get("blue_objectives", [])
            objs_html = _bullet_list([_na(o) for o in objs]) if objs else '<span class="gm-body">None defined.</span>'
            _card("Blue Objectives", objs_html)

        with col_r:
            red_text = _na(scenario.get("red_posture"), "No posture data.")
            _card("Red Posture", f'<div class="gm-body">{red_text}</div>')

        # Critical Systems table
        assets = scenario.get("assets", [])
        if assets:
            rows_html = "".join(
                f"""<tr>
                    <td>{_na(a.get('name'))}</td>
                    <td>{_asset_function(a)}</td>
                    <td>{STATUS_CHIP.get(a.get('status','online'), '<span class="chip chip-white">' + _na(a.get('status')) + '</span>')}</td>
                    <td>{_asset_risk(a)}</td>
                </tr>"""
                for a in assets
            )
            table_html = f"""
            <table class="gm-table">
                <colgroup>
                    <col style="width:28%">
                    <col style="width:32%">
                    <col style="width:22%">
                    <col style="width:18%">
                </colgroup>
                <thead>
                    <tr>
                        <th>System</th>
                        <th>Function</th>
                        <th>Status</th>
                        <th>Risk</th>
                    </tr>
                </thead>
                <tbody>{rows_html}</tbody>
            </table>"""
            _card("Critical Systems", table_html)

        # ── Intel Feed (fused scenario data) ──────────────────────────────────
        tension_score = scenario.get("tension_score", 0)
        conflict_score = scenario.get("conflict_score", 0)
        infra_risk = scenario.get("infrastructure_risk_score", 0)
        agg_score = scenario.get("adversary_aggression_score", 0)
        scenario_summary_text = scenario.get("scenario_summary", "")
        doctrine_notes = scenario.get("doctrine_notes", [])
        strategic_notes = scenario.get("strategic_notes", [])
        infra_records = scenario.get("infrastructure", [])
        red_posture_label = scenario.get("recommended_red_posture", "")
        recent_events = scenario.get("recent_events", [])

        has_intel = any([tension_score, scenario_summary_text, doctrine_notes, infra_records, recent_events])

        if has_intel:
            st.markdown('<div class="gm-section-label" style="margin-top:18px;margin-bottom:8px">Intelligence Fusion</div>', unsafe_allow_html=True)

            # Score row
            def _score_bar(val: int, color: str = "#b03030") -> str:
                pct = max(0, min(100, val))
                return (
                    f'<div style="display:flex;align-items:center;gap:8px">'
                    f'<div style="flex:1;height:6px;background:#1a2230;border-radius:3px;overflow:hidden">'
                    f'<div style="width:{pct}%;height:100%;background:{color};border-radius:3px"></div></div>'
                    f'<span style="font-size:0.75rem;color:#8a97a8;min-width:30px;text-align:right">{pct}</span>'
                    f'</div>'
                )

            scores_html = f"""
            <table style="width:100%;border-collapse:collapse">
              <tr>
                <td style="padding:4px 12px 4px 0;color:#5a6a7a;font-size:0.72rem;letter-spacing:0.06em;text-transform:uppercase;width:180px">Tension Score</td>
                <td style="padding:4px 0">{_score_bar(tension_score, "#b03030")}</td>
              </tr>
              <tr>
                <td style="padding:4px 12px 4px 0;color:#5a6a7a;font-size:0.72rem;letter-spacing:0.06em;text-transform:uppercase">Conflict Intensity</td>
                <td style="padding:4px 0">{_score_bar(conflict_score, "#c04a20")}</td>
              </tr>
              <tr>
                <td style="padding:4px 12px 4px 0;color:#5a6a7a;font-size:0.72rem;letter-spacing:0.06em;text-transform:uppercase">Infrastructure Risk</td>
                <td style="padding:4px 0">{_score_bar(infra_risk, "#a06020")}</td>
              </tr>
              <tr>
                <td style="padding:4px 12px 4px 0;color:#5a6a7a;font-size:0.72rem;letter-spacing:0.06em;text-transform:uppercase">Adversary Aggression</td>
                <td style="padding:4px 0">{_score_bar(agg_score, "#7030a0")}</td>
              </tr>
            </table>"""

            posture_chip = ""
            if red_posture_label == "aggressive":
                posture_chip = '<span class="chip chip-red">AGGRESSIVE</span>'
            elif red_posture_label == "opportunistic":
                posture_chip = '<span class="chip chip-amber">OPPORTUNISTIC</span>'
            elif red_posture_label == "conservative":
                posture_chip = '<span class="chip chip-green">CONSERVATIVE</span>'

            scores_header = f"Signal Scores {posture_chip}" if posture_chip else "Signal Scores"
            _card(scores_header, scores_html)

            # Scenario summary
            if scenario_summary_text:
                _card("Scenario Summary", f'<div class="gm-body">{scenario_summary_text}</div>')

            col_doc, col_strat = st.columns(2)

            # Doctrine notes
            with col_doc:
                if doctrine_notes:
                    notes_html = _bullet_list(doctrine_notes)
                    _card("Doctrine Grounding (JP 3-12 / JP 5-0)", notes_html)

            # Strategic notes
            with col_strat:
                if strategic_notes:
                    strat_html = _bullet_list(strategic_notes)
                    _card("Strategic Assessment (CSIS)", strat_html)

            # Infrastructure at risk from OSM
            if infra_records:
                infra_rows = "".join(
                    f"""<tr>
                        <td>{r.get('name', '—')}</td>
                        <td style="color:#8a97a8">{r.get('type', '—').replace('_', ' ').title()}</td>
                        <td>{r.get('location', '—')}</td>
                        <td>{'<span class="chip chip-red">CRITICAL</span>' if r.get('criticality') == 'critical' else '<span class="chip chip-amber">HIGH</span>' if r.get('criticality') == 'high' else '<span class="chip chip-white">MED</span>'}</td>
                        <td style="color:#6a7a8a;font-size:0.72rem">{r.get('risk_label', '')[:80]}</td>
                    </tr>"""
                    for r in infra_records[:6]
                )
                infra_table = f"""
                <table class="gm-table">
                    <thead><tr>
                        <th>Facility</th><th>Type</th><th>Location</th><th>Criticality</th><th>Risk Context</th>
                    </tr></thead>
                    <tbody>{infra_rows}</tbody>
                </table>"""
                _card("Key Infrastructure at Risk (OSM/Overpass)", infra_table)

            # Recent intel events
            if recent_events:
                event_rows = "".join(
                    f"""<tr>
                        <td style="color:#5a6a7a;font-size:0.72rem">{ev.get('timestamp','')[:10] or '—'}</td>
                        <td style="color:#8a97a8;font-size:0.72rem;text-transform:uppercase">{ev.get('source','—')}</td>
                        <td style="color:#6a7a8a;font-size:0.72rem">{ev.get('location','—')}</td>
                        <td style="font-size:0.72rem">{ev.get('summary','—')[:120]}</td>
                    </tr>"""
                    for ev in recent_events[:6]
                )
                events_table = f"""
                <table class="gm-table">
                    <thead><tr><th>Date</th><th>Source</th><th>Location</th><th>Signal</th></tr></thead>
                    <tbody>{event_rows}</tbody>
                </table>"""
                _card("Recent Intelligence Signals (GDELT / Local Conflict)", events_table)

        _debug_json("Scenario raw data", scenario)


# ── Tab 2: Move ───────────────────────────────────────────────────────────────
with tab_move:
    st.markdown('<div class="gm-section-label" style="margin-bottom:6px">Submit Blue Move</div>', unsafe_allow_html=True)
    st.markdown('<div class="gm-body" style="margin-bottom:10px">Describe your cyber defensive action in plain English. The engine will parse, adjudicate, and generate a Red counter-move.</div>', unsafe_allow_html=True)

    blue_move = st.text_area(
        "Blue move",
        height=110,
        placeholder="e.g. Isolate the SCADA HMI from the corporate VLAN and hunt for persistence on the jump host",
        label_visibility="collapsed",
    )

    if st.button("Execute Move", use_container_width=True, type="primary"):
        if not blue_move.strip():
            st.warning("Enter a move first.")
        else:
            with st.spinner("Adjudicating…"):
                result = _post("/turn", {"blue_move": blue_move}, api_url)
            if result:
                st.session_state["last_result"] = result
                st.success(f"Turn {result['turn_id']} recorded — switch to Result or AAR.")

    if st.session_state["last_result"]:
        lr = st.session_state["last_result"]
        p   = lr["parsed"]
        adj = lr["adjudication"]
        red = lr["red"]

        # Move review panel
        move_html = format_parsed_move(p)
        _card(f"Move Review — Turn {lr['turn_id']}", move_html)

        # Analyst assumptions (collapsible)
        assumptions = p.get("assumptions", [])
        if assumptions:
            with st.expander("Analyst Assumptions"):
                assump_html = _bullet_list([_na(a) for a in assumptions])
                st.markdown(assump_html, unsafe_allow_html=True)

        _debug_json("Parsed move (raw)", p)
        _debug_json("Adjudication (raw)", adj)
        _debug_json("Red response (raw)", red)


# ── Tab 3: Result ─────────────────────────────────────────────────────────────
with tab_result:
    lr = st.session_state["last_result"]
    if not lr:
        st.markdown('<div class="gm-body" style="padding:20px 0">Submit a Blue move to see results.</div>', unsafe_allow_html=True)
    else:
        p   = lr["parsed"]
        adj = lr["adjudication"]
        red = lr["red"]
        summary = format_result_move_summary(p, adj, red)

        # Summary banner
        st.markdown(f"""
        <div class="gm-mission-header">
            <div>
                <div class="gm-mission-eyebrow">Turn {lr['turn_id']} — Result</div>
                <div class="gm-mission-title">
                    <span class="gm-value">{summary['action']}</span>
                    <span style="color:#3a4a5a;margin:0 7px;font-size:0.85rem">→</span>
                    <span class="gm-value">{summary['target']}</span>
                </div>
            </div>
            <div class="gm-mission-meta">
                <div class="gm-mission-metric">
                    <span class="gm-mission-metric-label">Success</span>
                    {summary['success_chip']}
                </div>
                <div class="gm-mission-metric">
                    <span class="gm-mission-metric-label">Detection Risk</span>
                    {summary['detect_chip']}
                </div>
                <div class="gm-mission-metric">
                    <span class="gm-mission-metric-label">Attribution Risk</span>
                    {summary['attr_chip']}
                </div>
                <div class="gm-mission-metric">
                    <span class="gm-mission-metric-label">Red Response</span>
                    {summary['esc_chip']}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)

        with col1:
            move_html = format_parsed_move(p)
            _card("Move Details", move_html)

            assumptions = p.get("assumptions", [])
            if assumptions:
                with st.expander("Analyst Assumptions"):
                    st.markdown(_bullet_list([_na(a) for a in assumptions]), unsafe_allow_html=True)

        with col2:
            adj_html = format_adjudication(adj)
            _card("Outcome Assessment", adj_html)

            with st.expander("Assessment Rationale"):
                st.markdown(f'<div class="gm-body">{_na(adj.get("rationale"))}</div>', unsafe_allow_html=True)

        with col3:
            red_html = format_red_response(red)
            _card("Red Cell Response", red_html)

            with st.expander("Red Team Rationale"):
                st.markdown(f'<div class="gm-body">{_na(red.get("rationale"))}</div>', unsafe_allow_html=True)

        _debug_json("Full turn result (raw)", lr)


# ── Tab 4: AAR ────────────────────────────────────────────────────────────────
with tab_aar:
    lr = st.session_state["last_result"]
    if not lr or not lr.get("aar"):
        st.markdown('<div class="gm-body" style="padding:20px 0">Submit a Blue move to generate the After-Action Review.</div>', unsafe_allow_html=True)
    else:
        aar = lr["aar"]
        p   = lr["parsed"]

        st.markdown(f"""
        <div class="gm-mission-header">
            <div>
                <div class="gm-mission-eyebrow">After-Action Review</div>
                <div class="gm-mission-title">Turn {lr['turn_id']} — {_na(p.get('action')).title()}</div>
            </div>
            <span class="chip chip-slate">AAR COMPLETE</span>
        </div>
        """, unsafe_allow_html=True)

        # Executive debrief body
        ui_text = format_aar(aar)
        if ui_text:
            _card("Executive Debrief", f'<div class="gm-body" style="line-height:1.7">{ui_text}</div>')
        else:
            st.markdown('<div class="gm-body">AAR text not available for this turn.</div>', unsafe_allow_html=True)

        # Sources (always present if available — no raw JSON label)
        citations = aar.get("citations") or []
        if citations:
            cite_html = "".join(
                f'<div style="padding:6px 0;border-bottom:1px solid #141c26;font-size:0.76rem"><strong style="color:#6a8aa0">{_na(c.get("source"))}</strong> <span style="color:#3e4e60">·</span> <span style="color:#5a6a7a">{_na(c.get("text",""))[:160]}…</span></div>'
                for c in citations[:5]
            )
            with st.expander(f"Sources ({len(citations)})"):
                st.markdown(cite_html, unsafe_allow_html=True)

        # Debug only — raw AAR hidden by default
        _debug_json("Full AAR (raw)", aar)


# ── Tab 5: Timeline ───────────────────────────────────────────────────────────
with tab_timeline:
    st.markdown('<div class="gm-section-label" style="margin-bottom:12px">Operational Turn Log</div>', unsafe_allow_html=True)
    history: Optional[List[Dict[str, Any]]] = _get("/history", api_url)

    if not history:
        st.markdown('<div class="gm-body" style="padding:20px 0">No turns yet. Submit a Blue move to start.</div>', unsafe_allow_html=True)
    else:
        for turn in reversed(history):
            entry = format_timeline_entry(turn)

            # Readable expander label — uses truncated labels, no raw keys or JSON
            label = f"Turn {entry['turn_id']}  ·  {entry['action_label'].upper()} → {entry['target_label'].upper()}  ·  {entry['success_pct']}"

            with st.expander(label):
                h1, h2, h3 = st.columns(3)

                with h1:
                    blue_html = f'<div class="gm-body" style="margin-bottom:10px">{entry["blue_move"]}</div>'
                    blue_html += _kv_row("Action",  _value_pill(entry["action"]))
                    blue_html += _kv_row("Target",  _value_pill(entry["target"]))
                    blue_html += _kv_row("Outcome", entry["outcome_chip"])
                    _card("Blue Move", blue_html)

                with h2:
                    adj_body = (
                        _kv_row("Success Probability", entry["outcome_chip"])
                        + _kv_row("Detection Risk",    entry["detection_chip"])
                        + _kv_row("Red Response",      entry["esc_chip"])
                        + _section_divider("Operational Effects")
                        + _bullet_list(entry["effects_list"])
                        # Rationale inline — avoids nested expander error
                        + _inline_collapsible("Assessment Rationale", entry["rationale"])
                    )
                    _card("Outcome", adj_body)

                with h3:
                    red_body = (
                        _kv_row("Red Response Level", entry["esc_chip"])
                        + _section_divider("Red Team Action")
                        + f'<div class="gm-body" style="margin-bottom:4px">{entry["red_action"]}</div>'
                        # Rationale inline — avoids nested expander error
                        + _inline_collapsible("Red Team Rationale", entry["red_rationale"])
                    )
                    _card("Red Cell Response", red_body)

                # AAR for this turn
                try:
                    aar_r = requests.get(f"{api_url}/aar/{turn['turn_id']}", timeout=5)
                    if aar_r.ok:
                        aar_data = aar_r.json().get("aar", {})
                        aar_text = format_aar(aar_data)
                        if aar_text:
                            cites = aar_data.get("citations") or []
                            cite_html = ""
                            if cites:
                                cite_html = _inline_collapsible(
                                    f"Sources ({len(cites)})",
                                    "".join(
                                        f'<div style="padding:4px 0;border-bottom:1px solid #141c26;font-size:0.75rem"><strong style="color:#6a8aa0">{_na(c.get("source"))}</strong> <span style="color:#3e4e60">·</span> <span style="color:#5a6a7a">{_na(c.get("text",""))[:130]}…</span></div>'
                                        for c in cites[:3]
                                    )
                                )
                            _card("After-Action Review",
                                  f'<div class="gm-body" style="line-height:1.65">{aar_text}</div>{cite_html}')
                except Exception:
                    pass

                # Debug — gated
                _debug_json(f"Turn {entry['turn_id']} raw data", turn)
