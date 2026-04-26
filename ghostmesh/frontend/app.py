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
   GHOSTMESH · COMMAND-CENTER UI  v2
   Deep navy + teal/cyan accent system
   ════════════════════════════════════════════ */

/* ── Reset & base ─────────────────────────── */
*, *::before, *::after { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"] {
    background-color: #080c12 !important;
    color: #e2eaf4 !important;
    font-family: 'Inter', 'SF Pro Text', 'Segoe UI', system-ui, sans-serif;
    font-size: 15px;
    -webkit-font-smoothing: antialiased;
}

[data-testid="stAppViewContainer"] > .main > .block-container {
    padding: 1.75rem 2rem 2.5rem !important;
    max-width: 1380px !important;
}

[data-testid="stSidebar"] {
    background-color: #060a10 !important;
    border-right: 1px solid #14213a !important;
}

[data-testid="stSidebar"] > div:first-child {
    padding: 1.25rem 1rem !important;
}

/* ── Tabs ──────────────────────────────────── */
[data-testid="stTabs"] button {
    font-size: 0.76rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.14em !important;
    text-transform: uppercase !important;
    color: #4a6a88 !important;
    border-bottom: 2px solid transparent !important;
    padding: 11px 22px 10px !important;
    transition: color 0.15s ease !important;
}

[data-testid="stTabs"] button[aria-selected="true"] {
    color: #e2eaf4 !important;
    border-bottom: 2px solid #38b2f0 !important;
    background: none !important;
}

[data-testid="stTabs"] button:hover:not([aria-selected="true"]) {
    color: #90b8d4 !important;
}

[data-testid="stTabs"] [role="tablist"] {
    border-bottom: 1px solid #14213a !important;
    gap: 0 !important;
    margin-bottom: 1.5rem !important;
}

/* ── Cards ──────────────────────────────────── */
.gm-card {
    background: #0d1520;
    border: 1px solid #1a2d44;
    border-radius: 10px;
    padding: 18px 22px 22px;
    margin-bottom: 14px;
    display: flex;
    flex-direction: column;
}

/* Featured card — glowing blue border */
.gm-card-featured {
    background: #0e1828;
    border: 1px solid #1e4070;
    border-radius: 10px;
    padding: 18px 22px 22px;
    margin-bottom: 14px;
    display: flex;
    flex-direction: column;
    box-shadow: 0 0 24px rgba(30, 100, 200, 0.12), 0 1px 0 rgba(56,178,240,0.08) inset;
}

.gm-card-header {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: #38b2f0;
    margin-bottom: 14px;
    padding-bottom: 9px;
    border-bottom: 1px solid #1a2d44;
    flex-shrink: 0;
}

.gm-card-body { flex: 1; }

.gm-body {
    font-size: 0.9rem;
    color: #b0c8e0;
    line-height: 1.7;
}

/* ── Mission header banner ──────────────────── */
.gm-mission-header {
    background: linear-gradient(135deg, #0d1828 0%, #0a1420 100%);
    border: 1px solid #1e4070;
    border-left: 4px solid #38b2f0;
    border-radius: 10px;
    padding: 18px 24px;
    margin-bottom: 18px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 14px;
    box-shadow: 0 2px 20px rgba(30, 100, 200, 0.1);
}

.gm-mission-eyebrow {
    font-size: 0.62rem;
    font-weight: 700;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #38b2f0;
    margin-bottom: 6px;
    opacity: 0.8;
}

.gm-mission-title {
    font-size: 1.3rem;
    font-weight: 700;
    letter-spacing: 0.01em;
    color: #e2eaf4;
    line-height: 1.3;
}

.gm-mission-meta {
    display: flex;
    align-items: center;
    gap: 20px;
    flex-wrap: wrap;
}

.gm-mission-metric {
    text-align: center;
    flex-shrink: 0;
}

.gm-mission-metric-label {
    display: block;
    font-size: 0.58rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #4a6a88;
    margin-bottom: 5px;
}

/* ── Status chips / badges ──────────────────── */
.chip {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 0.67rem;
    font-weight: 800;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    padding: 5px 11px 4px;
    border-radius: 5px;
    white-space: nowrap;
    line-height: 1.4;
}
.chip-red    { background: #2a0a0a; color: #f06060; border: 1px solid #6a1818; }
.chip-amber  { background: #201400; color: #e09020; border: 1px solid #604000; }
.chip-green  { background: #061410; color: #30c090; border: 1px solid #0c4830; }
.chip-blue   { background: #081830; color: #38b2f0; border: 1px solid #104878; }
.chip-teal   { background: #061820; color: #20d4c0; border: 1px solid #0c4848; }
.chip-slate  { background: #0c1628; color: #6090b8; border: 1px solid #1c3050; }
.chip-white  { background: #121a28; color: #8090a8; border: 1px solid #202e40; }
.chip-orange { background: #201000; color: #e06818; border: 1px solid #502800; }

/* ── Table ──────────────────────────────────── */
.gm-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
    table-layout: fixed;
}
.gm-table colgroup col:nth-child(1) { width: 28%; }
.gm-table colgroup col:nth-child(2) { width: 30%; }
.gm-table colgroup col:nth-child(3) { width: 22%; }
.gm-table colgroup col:nth-child(4) { width: 20%; }

.gm-table th {
    font-size: 0.64rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #5898c0;
    padding: 11px 13px 10px;
    border-bottom: 1px solid #1a2d44;
    text-align: left;
    white-space: nowrap;
    background: rgba(20, 50, 90, 0.3);
}
.gm-table td {
    padding: 13px 13px;
    border-bottom: 1px solid #101c2a;
    color: #b0c8e0;
    vertical-align: middle;
    word-break: break-word;
    line-height: 1.5;
}
.gm-table tr:last-child td { border-bottom: none; }
.gm-table tr:hover td { background: #0f1e30; }
.gm-table td:first-child { color: #d4e4f4; font-weight: 600; }

/* ── Key-value rows ─────────────────────────── */
.gm-kv-row {
    display: flex;
    align-items: flex-start;
    padding: 9px 0 8px;
    border-bottom: 1px solid #101c2a;
    gap: 14px;
    min-height: 36px;
}
.gm-kv-row:last-child { border-bottom: none; }

.gm-kv-key {
    min-width: 152px;
    max-width: 152px;
    color: #5898c0;
    font-size: 0.73rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    padding-top: 2px;
    flex-shrink: 0;
    line-height: 1.4;
}
.gm-kv-val {
    color: #c8daea;
    font-size: 0.87rem;
    line-height: 1.5;
    word-break: break-word;
    flex: 1;
}

/* ── Sub-section divider inside a card ─────── */
.gm-sub-header {
    font-size: 0.62rem;
    font-weight: 700;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: #38b2f0;
    padding: 12px 0 7px;
    border-bottom: 1px solid #1a2d44;
    margin-bottom: 4px;
    opacity: 0.75;
}

/* ── Bullet list ────────────────────────────── */
.gm-bullet-list {
    list-style: none;
    margin: 0;
    padding: 0;
}
.gm-bullet-list li {
    padding: 6px 0 5px;
    border-bottom: 1px solid #101c2a;
    font-size: 0.87rem;
    color: #b0c8e0;
    line-height: 1.65;
    padding-left: 18px;
    position: relative;
}
.gm-bullet-list li:last-child { border-bottom: none; }
.gm-bullet-list li::before {
    content: "▸";
    color: #38b2f0;
    position: absolute;
    left: 0;
    top: 6px;
    font-size: 0.68rem;
}

/* ── Value pill ─────────────────────────────── */
.gm-value {
    display: inline-block;
    background: #081830;
    color: #60c0f0;
    font-size: 0.84rem;
    padding: 3px 11px 2px;
    border-radius: 5px;
    border: 1px solid #104870;
    font-weight: 500;
    white-space: nowrap;
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* ── Section label (page-level) ─────────────── */
.gm-section-label {
    font-size: 0.62rem;
    font-weight: 700;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #38b2f0;
    margin-bottom: 10px;
    margin-top: 2px;
    opacity: 0.75;
}

/* ── Metric row ─────────────────────────────── */
.gm-metric-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 0;
    border-bottom: 1px solid #101c2a;
    font-size: 0.84rem;
}
.gm-metric-label { color: #5898c0; font-size: 0.73rem; text-transform: uppercase; letter-spacing: 0.08em; }
.gm-metric-value { font-weight: 700; font-size: 0.88rem; }

/* ── Sidebar ────────────────────────────────── */
[data-testid="stSidebar"] .stTextInput input,
[data-testid="stSidebar"] .stSelectbox select,
[data-testid="stSidebar"] .stTextArea textarea {
    background: #080c14 !important;
    border: 1px solid #1a2d44 !important;
    color: #b0c8e0 !important;
    font-size: 0.84rem !important;
    border-radius: 6px !important;
}

[data-testid="stSidebar"] label {
    font-size: 0.68rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    color: #5898c0 !important;
}

/* ── Sidebar navigation ─────────────────────── */
.gm-nav {
    display: flex;
    flex-direction: column;
    gap: 1px;
    margin-bottom: 4px;
}
.gm-nav-item {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 0.82rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    color: #587890;
    padding: 8px 12px;
    border-radius: 6px;
    border: 1px solid transparent;
    cursor: default;
}
.gm-nav-icon {
    width: 18px;
    height: 18px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 0.8rem;
    opacity: 0.7;
}

/* ── Buttons ────────────────────────────────── */
[data-testid="stButton"] button[kind="primary"] {
    background: linear-gradient(135deg, #1a5aaa 0%, #1040888 100%) !important;
    background: #1652a0 !important;
    color: #e8f4ff !important;
    border: 1px solid #2a78d0 !important;
    border-radius: 7px !important;
    font-size: 0.8rem !important;
    font-weight: 800 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    padding: 0.65rem 1.3rem !important;
    transition: all 0.15s ease !important;
    box-shadow: 0 2px 12px rgba(38, 120, 200, 0.35) !important;
}
[data-testid="stButton"] button[kind="primary"]:hover {
    background: #1e6ac0 !important;
    box-shadow: 0 4px 20px rgba(38, 120, 200, 0.5) !important;
}

[data-testid="stButton"] button[kind="secondary"],
[data-testid="stButton"] button:not([kind]) {
    background: #0c1520 !important;
    color: #6a8898 !important;
    border: 1px solid #1a2d44 !important;
    border-radius: 7px !important;
    font-size: 0.73rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    padding: 0.52rem 1.1rem !important;
    transition: all 0.12s ease !important;
}
[data-testid="stButton"] button[kind="secondary"]:hover,
[data-testid="stButton"] button:not([kind]):hover {
    background: #111e30 !important;
    color: #90aac0 !important;
    border-color: #243a58 !important;
}

/* ── Expanders ──────────────────────────────── */
[data-testid="stExpander"] {
    background: #0a1420 !important;
    border: 1px solid #1a2d44 !important;
    border-radius: 7px !important;
    margin-top: 8px !important;
}
[data-testid="stExpander"] summary {
    font-size: 0.73rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.08em !important;
    color: #5898c0 !important;
    padding: 11px 15px !important;
}
[data-testid="stExpander"] > div[data-testid="stExpanderDetails"] {
    padding: 4px 15px 14px !important;
}

/* ── Alerts ─────────────────────────────────── */
[data-testid="stAlert"] {
    font-size: 0.84rem !important;
    border-radius: 6px !important;
    padding: 10px 14px !important;
}

/* ── Streamlit chrome cleanup — hide Deploy & toolbar ── */
[data-testid="stHeader"]      { background: transparent !important; }
[data-testid="stDecoration"]  { display: none !important; }
[data-testid="stToolbar"]     { display: none !important; visibility: hidden !important; }
[data-testid="stStatusWidget"]{ display: none !important; }
[data-testid="stToolbarActions"] { display: none !important; }
.stDeployButton               { display: none !important; }
.stApp > header               { display: none !important; }
#MainMenu                     { visibility: hidden !important; display: none !important; }
footer                        { visibility: hidden !important; display: none !important; }

/* ── Text area ──────────────────────────────── */
.stTextArea textarea {
    background: #080c14 !important;
    border: 1px solid #1a2d44 !important;
    color: #b0c8e0 !important;
    font-size: 0.88rem !important;
    border-radius: 6px !important;
    line-height: 1.7 !important;
}

/* ── Divider ────────────────────────────────── */
hr { border-color: #14213a !important; opacity: 1 !important; margin: 0.75rem 0 !important; }

/* ── Progress bar ───────────────────────────── */
[data-testid="stProgressBar"] > div > div { background: #38b2f0 !important; }

/* ── Sidebar wordmark ───────────────────────── */
.gm-wordmark {
    font-size: 0.92rem;
    font-weight: 900;
    letter-spacing: 0.24em;
    text-transform: uppercase;
    color: #e0eef8;
}
.gm-wordmark-sub {
    font-size: 0.58rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #28486a;
    margin-top: 4px;
}

/* ── Sidebar scenario status ────────────────── */
.gm-scenario-status {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 9px;
}
.gm-scenario-label {
    font-size: 0.64rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #5898c0;
}

/* ── Column containers ──────────────────────── */
[data-testid="column"] { padding: 0 6px !important; }

/* ── Confidence / parser warning note ──────── */
.gm-confidence-note {
    background: #140e00;
    border: 1px solid #503800;
    border-left: 3px solid #c07818;
    border-radius: 6px;
    padding: 10px 15px;
    font-size: 0.82rem;
    color: #b07828;
    margin-top: 12px;
    line-height: 1.55;
}

/* ── Dim note (empty state inside cards) ───── */
.gm-dim-note {
    color: #2a3a4a;
    font-size: 0.80rem;
    font-style: italic;
}

/* ── Inline collapsible (timeline expanders) ── */
details.gm-details {
    margin-top: 8px;
    border: 1px solid #1a2d44;
    border-radius: 6px;
    background: #0a1420;
}
details.gm-details summary {
    cursor: pointer;
    padding: 8px 13px;
    font-size: 0.73rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #5898c0;
    list-style: none;
    user-select: none;
}
details.gm-details summary::-webkit-details-marker { display: none; }
details.gm-details summary::before {
    content: "▸ ";
    color: #38b2f0;
    font-size: 0.62rem;
}
details.gm-details[open] summary::before { content: "▾ "; }
details.gm-details .gm-details-body {
    padding: 8px 15px 13px;
    border-top: 1px solid #1a2d44;
}

/* ── Top nav tab buttons (first stHorizontalBlock in main area) ─────────── */
.main [data-testid="stHorizontalBlock"]:first-of-type [data-testid="stButton"] button,
.main [data-testid="stHorizontalBlock"]:first-of-type [data-testid="stButton"] button:focus,
.main [data-testid="stHorizontalBlock"]:first-of-type [data-testid="stButton"] button:active {
    background: transparent !important;
    color: #4a6a88 !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    border-radius: 0 !important;
    font-size: 0.75rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.14em !important;
    text-transform: uppercase !important;
    padding: 12px 4px 10px !important;
    width: 100% !important;
    box-shadow: none !important;
    outline: none !important;
    transition: color 0.15s ease, border-color 0.15s ease !important;
}
.main [data-testid="stHorizontalBlock"]:first-of-type [data-testid="stButton"] button:hover {
    background: transparent !important;
    color: #90b8d4 !important;
    border-bottom: 2px solid #2a5a80 !important;
    box-shadow: none !important;
}

/* ── Sidebar nav buttons ─────────────────────── */
[data-testid="stSidebar"] [data-testid="stButton"] button,
[data-testid="stSidebar"] [data-testid="stButton"] button:focus,
[data-testid="stSidebar"] [data-testid="stButton"] button:active {
    background: transparent !important;
    color: #587890 !important;
    border: 1px solid transparent !important;
    border-radius: 6px !important;
    font-size: 0.84rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.04em !important;
    text-transform: none !important;
    padding: 8px 12px !important;
    text-align: left !important;
    width: 100% !important;
    box-shadow: none !important;
    transition: all 0.12s ease !important;
}
[data-testid="stSidebar"] [data-testid="stButton"] button:hover {
    background: #0f1e30 !important;
    color: #90c0e0 !important;
    border-color: #1a3050 !important;
    box-shadow: none !important;
}

/* ── Force-override: top nav buttons must look like tabs, not buttons ── */
/* This block comes LAST to win specificity over generic button rules */
.block-container [data-testid="stHorizontalBlock"]:first-of-type button,
.block-container [data-testid="stHorizontalBlock"]:first-of-type button:hover,
.block-container [data-testid="stHorizontalBlock"]:first-of-type button:focus,
.block-container [data-testid="stHorizontalBlock"]:first-of-type button:active {
    background: transparent !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    font-size: 0.75rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.14em !important;
    text-transform: uppercase !important;
    color: #4a6a88 !important;
    padding: 12px 4px 10px !important;
    outline: none !important;
}

/* ── Responsive: 1366px & narrower ─────────── */
@media screen and (max-width: 1400px) {
    [data-testid="stAppViewContainer"] > .main > .block-container {
        padding: 1.5rem 1.5rem 2rem !important;
    }
    .gm-kv-key { min-width: 128px; max-width: 128px; }
    .gm-table { font-size: 0.81rem; }
    .gm-table td, .gm-table th { padding: 10px 11px; }
    .gm-mission-title { font-size: 1.1rem; }
    [data-testid="column"] { padding: 0 4px !important; }
}
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "last_result" not in st.session_state:
    st.session_state["last_result"] = None
if "active_scenario_id" not in st.session_state:
    st.session_state["active_scenario_id"] = None
if "active_tab" not in st.session_state:
    st.session_state["active_tab"] = "BRIEF"

# ── Constants ─────────────────────────────────────────────────────────────────
STATUS_CHIP = {
    "at-risk":          '<span class="chip chip-orange">⚠ AT-RISK</span>',
    "compromised":      '<span class="chip chip-red">✕ COMPROMISED</span>',
    "clean":            '<span class="chip chip-green">✓ CLEAN</span>',
    "online":           '<span class="chip chip-green">✓ ONLINE</span>',
    "patching-pending": '<span class="chip chip-amber">↻ PATCHING</span>',
    "defaced":          '<span class="chip chip-red">✕ DEFACED</span>',
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
    if v is None:
        return default
    if isinstance(v, (dict, list)):
        return "See detailed view"
    s = str(v).strip()
    if not s:
        return default
    if s.lower() in ("none", "null", "undefined", "unknown", "n/a", "na"):
        return "Needs analyst review"
    return s


def _safe_float(v: Any, default: float = 0.0) -> float:
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
        return '<span class="chip chip-red">🔴 CRITICAL</span>'
    if status in ("at-risk", "patching-pending"):
        return '<span class="chip chip-orange">🟠 ELEVATED</span>'
    return '<span class="chip chip-green">🟢 NOMINAL</span>'


def _clean_effect(e: Any) -> str:
    if isinstance(e, dict):
        desc = e.get("description") or e.get("text") or e.get("effect") or ""
        s = str(desc).strip()
        return s if s else "Effect details not available"
    if isinstance(e, str):
        cleaned = e.split("] ", 1)[-1] if "] " in e else e
        return cleaned.strip() or "Effect details not available"
    return "Effect details not available"


def _strip_markdown(text: str) -> str:
    text = re.sub(r"```[\s\S]*?```", "[code block removed]", text)
    text = re.sub(r"`[^`\n]+`", lambda m: m.group(0)[1:-1], text)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\*{1,2}([^*\n]+)\*{1,2}", r"\1", text)
    text = re.sub(r"_{1,2}([^_\n]+)_{1,2}", r"\1", text)
    text = re.sub(r"^[\*\-]\s+", "• ", text, flags=re.MULTILINE)
    text = "\n".join(line.rstrip() for line in text.splitlines())
    return text.strip()


def _value_pill(text: str) -> str:
    return f'<span class="gm-value">{_na(text)}</span>'


def _kv_row(label: str, value_html: str) -> str:
    return f'<div class="gm-kv-row"><span class="gm-kv-key">{label}</span><span class="gm-kv-val">{value_html}</span></div>'


def _section_divider(label: str) -> str:
    return f'<div class="gm-sub-header">{label}</div>'


def _bullet_list(items: List[str], pre_rendered: bool = False) -> str:
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
    if not aar or not isinstance(aar, dict):
        return ""
    ui_text = aar.get("ui_text") or ""
    if not isinstance(ui_text, str):
        return ""
    return _strip_markdown(ui_text)


def format_timeline_entry(turn: Dict) -> Dict[str, Any]:
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
    return f"""<details class="gm-details">
  <summary>{summary}</summary>
  <div class="gm-details-body gm-body">{body_html}</div>
</details>"""


def _card(header: str, body_html: str, featured: bool = False) -> None:
    css_class = "gm-card-featured" if featured else "gm-card"
    st.markdown(f"""
    <div class="{css_class}">
        <div class="gm-card-header">{header}</div>
        <div class="gm-card-body">{body_html}</div>
    </div>
    """, unsafe_allow_html=True)


def _debug_json(label: str, data: Any) -> None:
    """No-op — debug output removed for demo."""
    pass


# ── HTTP helpers ──────────────────────────────────────────────────────────────

_DEFAULT_GET_TIMEOUT_S = 12
_DEFAULT_POST_TIMEOUT_S = 45
_TIMEOUT_OVERRIDES_S: Dict[str, int] = {
    "/turn": 90,
    "/scenarios/seed": 60,
}


def _get(path: str, api_url: str) -> Optional[Any]:
    try:
        r = requests.get(f"{api_url}{path}", timeout=_DEFAULT_GET_TIMEOUT_S)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error(f"Cannot reach API at {api_url}. Is the backend running?")
        return None
    except requests.exceptions.ReadTimeout:
        st.error(f"API request timed out after {_DEFAULT_GET_TIMEOUT_S}s: {path}")
        return None
    except Exception as e:
        st.error(f"API error: {e}")
        return None


def _post(path: str, payload: Dict[str, Any], api_url: str) -> Optional[Any]:
    timeout_s = _TIMEOUT_OVERRIDES_S.get(path, _DEFAULT_POST_TIMEOUT_S)
    try:
        r = requests.post(f"{api_url}{path}", json=payload, timeout=timeout_s)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error(f"Cannot reach API at {api_url}.")
        return None
    except requests.exceptions.ReadTimeout:
        st.error(f"API request timed out after {timeout_s}s: {path}")
        return None
    except requests.exceptions.HTTPError as e:
        detail = r.json().get("detail", str(e)) if r.content else str(e)
        st.error(f"API error: {detail}")
        return None
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return None


# ── Sidebar ───────────────────────────────────────────────────────────────────
API_URL = "http://localhost:8029"

with st.sidebar:
    # ── Wordmark ──────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="padding:10px 0 14px 0">
        <div class="gm-wordmark">GhostMesh</div>
        <div class="gm-wordmark-sub">AI Cyber Wargaming Engine</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<hr style="margin:0 0 14px 0">', unsafe_allow_html=True)

    # ── Navigation ────────────────────────────────────────────────────────────
    st.markdown('<div class="gm-section-label">Navigation</div>', unsafe_allow_html=True)

    _nav_items = [
        ("BRIEF",    "📋", "Brief"),
        ("MOVE",     "⚔",  "Move"),
        ("RESULT",   "📊", "Result"),
        ("AAR",      "📄", "AAR"),
        ("TIMELINE", "📅", "Timeline"),
    ]
    _active = st.session_state["active_tab"]
    for _tab_key, _icon, _label in _nav_items:
        _is_active = _tab_key == _active
        _btn_style = (
            "background:#122040;color:#38b2f0;border:1px solid #1e4070;border-radius:6px;"
            "padding:9px 12px;width:100%;text-align:left;cursor:pointer;"
            "font-size:0.83rem;font-weight:700;letter-spacing:0.04em;margin-bottom:2px;display:block;"
        ) if _is_active else (
            "background:transparent;color:#587890;border:1px solid transparent;border-radius:6px;"
            "padding:9px 12px;width:100%;text-align:left;cursor:pointer;"
            "font-size:0.83rem;font-weight:600;letter-spacing:0.04em;margin-bottom:2px;display:block;"
        )
        if st.button(f"{_icon}  {_label}", key=f"nav_{_tab_key}", use_container_width=True):
            st.session_state["active_tab"] = _tab_key
            st.rerun()

    st.markdown('<hr style="margin:10px 0 14px 0">', unsafe_allow_html=True)

    # ── Scenario selector + status badge ──────────────────────────────────────
    scenarios_list: List[Dict] = _get("/scenarios", API_URL) or []
    scenario_names = [s["name"] for s in scenarios_list]
    scenario_ids   = [s["id"]   for s in scenarios_list]

    current_idx = 0
    if st.session_state["active_scenario_id"] in scenario_ids:
        current_idx = scenario_ids.index(st.session_state["active_scenario_id"])

    # Derive status badge from active scenario tension
    _active_scenario = _get("/scenario", API_URL) if st.session_state["active_scenario_id"] else None
    _tension = (_active_scenario or {}).get("tension_level", 0.5)
    if _tension >= 0.7:
        _status_badge = '<span class="chip chip-red" style="font-size:0.6rem;padding:4px 9px">🔴 CRITICAL</span>'
    elif _tension >= 0.45:
        _status_badge = '<span class="chip chip-orange" style="font-size:0.6rem;padding:4px 9px">🟠 ELEVATED</span>'
    else:
        _status_badge = '<span class="chip chip-green" style="font-size:0.6rem;padding:4px 9px">🟢 NOMINAL</span>'

    _live_scenario_name = scenarios_list[current_idx]["name"] if scenarios_list else "No scenario loaded"
    st.markdown(f"""
    <div class="gm-scenario-status">
        <span class="gm-scenario-label">Live Scenario</span>
        {_status_badge}
    </div>
    <div class="gm-dim-note" style="font-size:0.82rem;padding:4px 0 8px 0;font-weight:600;color:#e2e8f0">{_live_scenario_name}</div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="gm-section-label" style="margin-top:14px">New Scenario</div>', unsafe_allow_html=True)
    scenario_query = st.text_input(
        "Scenario",
        placeholder="e.g. Volt Typhoon Texas power grid",
        key="scenario_input",
        label_visibility="collapsed",
    )
    st.caption("GDELT · LiveUAMap · UCDP · GTD · OSM · OpenTopography · JCS doctrine")

    st.markdown('<div style="margin-top:10px"></div>', unsafe_allow_html=True)
    if st.button("⚡ Launch Scenario", use_container_width=True, type="primary"):
        if scenario_query.strip():
            with st.spinner("Fusing live intelligence…"):
                seeded = _post("/scenarios/seed", {"query": scenario_query.strip(), "use_api": True}, API_URL)
            if seeded:
                sources = " · ".join(s.upper() for s in seeded.get("sources_used", [])) or "SEED"
                st.success(f"✓ {sources} — **{seeded['name']}**")
                st.session_state["active_scenario_id"] = seeded.get("id", "")
                st.rerun()
        else:
            st.warning("Enter a scenario query first.")

    st.markdown('<hr style="margin:12px 0">', unsafe_allow_html=True)

    if st.button("Reset Session", use_container_width=True):
        r = _post("/reset", {}, API_URL)
        if r:
            st.session_state["last_result"] = None
            st.success("Session cleared.")
            st.rerun()

    st.markdown(
        '<div style="padding-top:12px"><span style="font-size:0.58rem;letter-spacing:0.1em;'
        'text-transform:uppercase;color:#2a3a4a">Blue Team Interface · Plain English Only</span></div>',
        unsafe_allow_html=True,
    )


# ── Tab bar (mirrors sidebar nav) ─────────────────────────────────────────────
_active_tab = st.session_state["active_tab"]
_tab_labels = ["BRIEF", "MOVE", "RESULT", "AAR", "TIMELINE"]

_tab_cols = st.columns(len(_tab_labels))
for _col, _lbl in zip(_tab_cols, _tab_labels):
    with _col:
        if st.button(_lbl, key=f"topnav_{_lbl}", use_container_width=True):
            st.session_state["active_tab"] = _lbl
            st.rerun()

st.markdown('<hr style="margin:-4px 0 22px 0;border-color:#14213a">', unsafe_allow_html=True)

# JS: highlight the active top-nav button
st.markdown(f"""
<script>
(function() {{
  function styleNav() {{
    // Target only the top nav row buttons (not sidebar)
    var rows = document.querySelectorAll('.gm-topnav-row [data-testid="stButton"] button');
    rows.forEach(function(b) {{
      if (b.innerText.trim() === "{_active_tab}") {{
        b.style.cssText += ';color:#e2eaf4!important;border-bottom:2px solid #38b2f0!important;';
      }}
    }});
    // Style sidebar nav active item
    var sidebtns = document.querySelectorAll('[data-testid="stSidebar"] [data-testid="stButton"] button');
    sidebtns.forEach(function(b) {{
      var txt = b.innerText.trim().split('  ').pop().toUpperCase();
      if (txt === "{_active_tab}") {{
        b.style.background = '#122040';
        b.style.color = '#38b2f0';
        b.style.borderColor = '#1e4070';
      }}
    }});
  }}
  setTimeout(styleNav, 80);
  setTimeout(styleNav, 400);
}})();
</script>
""", unsafe_allow_html=True)

# ── Tab content ───────────────────────────────────────────────────────────────
_active_tab = st.session_state["active_tab"]

# ── Tab 1: Brief ──────────────────────────────────────────────────────────────
if _active_tab == "BRIEF":
    scenario = _get("/scenario", API_URL)
    if not scenario:
        st.markdown('<div class="gm-body" style="padding:24px 0">No active scenario. Select or create one from the sidebar.</div>', unsafe_allow_html=True)
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

        # Situation summary — featured card
        # Prefer the fused intelligence summary because it is query-specific and
        # changes as users launch new scenarios.
        primary_summary = _na(
            scenario.get("scenario_summary") or scenario.get("brief"),
            "No scenario summary available.",
        )
        _card("Scenario Summary", f'<div class="gm-body">{primary_summary}</div>', featured=True)

        # Two-column: objectives + red posture
        col_l, col_r = st.columns(2)

        with col_l:
            objs = scenario.get("blue_objectives", [])
            objs_html = _bullet_list([_na(o) for o in objs]) if objs else '<span class="gm-body">None defined.</span>'
            _card("Blue Objectives", objs_html)

        with col_r:
            red_text = _na(scenario.get("red_posture"), "No posture data.")
            _card("Red Posture", f'<div class="gm-body">{red_text}</div>', featured=True)

        # Critical Systems table — featured card
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
            _card("Critical Systems", table_html, featured=True)

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
            st.markdown('<div class="gm-section-label" style="margin-top:22px;margin-bottom:10px">Intelligence Fusion</div>', unsafe_allow_html=True)

            def _score_bar(val: int, grad: str) -> str:
                pct = max(0, min(100, val))
                return (
                    f'<div style="display:flex;align-items:center;gap:12px">'
                    f'<div style="flex:1;height:8px;background:#0d1828;border-radius:4px;overflow:hidden;border:1px solid #14213a">'
                    f'<div style="width:{pct}%;height:100%;background:{grad};border-radius:4px"></div></div>'
                    f'<span style="font-size:0.8rem;font-weight:700;color:#c8daea;min-width:38px;text-align:right">{pct} / 100</span>'
                    f'</div>'
                )

            scores_html = f"""
            <table style="width:100%;border-collapse:collapse">
              <tr>
                <td style="padding:8px 16px 8px 0;color:#5898c0;font-size:0.73rem;letter-spacing:0.08em;text-transform:uppercase;width:200px;font-weight:700">Tension Score</td>
                <td style="padding:8px 0">{_score_bar(tension_score, "linear-gradient(90deg,#c03030,#f06060)")}</td>
              </tr>
              <tr>
                <td style="padding:8px 16px 8px 0;color:#5898c0;font-size:0.73rem;letter-spacing:0.08em;text-transform:uppercase;font-weight:700">Conflict Intensity</td>
                <td style="padding:8px 0">{_score_bar(conflict_score, "linear-gradient(90deg,#c04a20,#e08840)")}</td>
              </tr>
              <tr>
                <td style="padding:8px 16px 8px 0;color:#5898c0;font-size:0.73rem;letter-spacing:0.08em;text-transform:uppercase;font-weight:700">Infrastructure Risk</td>
                <td style="padding:8px 0">{_score_bar(infra_risk, "linear-gradient(90deg,#806010,#c0a030)")}</td>
              </tr>
              <tr>
                <td style="padding:8px 16px 8px 0;color:#5898c0;font-size:0.73rem;letter-spacing:0.08em;text-transform:uppercase;font-weight:700">Adversary Aggression</td>
                <td style="padding:8px 0">{_score_bar(agg_score, "linear-gradient(90deg,#6020a0,#a060e0)")}</td>
              </tr>
            </table>"""

            posture_chip = ""
            if red_posture_label == "aggressive":
                posture_chip = '<span class="chip chip-red">SIGNAL SCORE: AGGRESSIVE</span>'
            elif red_posture_label == "opportunistic":
                posture_chip = '<span class="chip chip-amber">SIGNAL SCORE: OPPORTUNISTIC</span>'
            elif red_posture_label == "conservative":
                posture_chip = '<span class="chip chip-teal">SIGNAL SCORE: CONSERVATIVE</span>'

            scores_header = f"Intelligence Fusion &nbsp;&nbsp;{posture_chip}" if posture_chip else "Intelligence Fusion"
            _card(scores_header, scores_html)

            # Avoid duplicate summary cards when the featured card already shows
            # the same fused narrative.
            if scenario_summary_text and scenario_summary_text.strip() != primary_summary.strip():
                _card("Scenario Summary", f'<div class="gm-body">{scenario_summary_text}</div>')

            col_doc, col_strat = st.columns(2)

            with col_doc:
                if doctrine_notes:
                    _card("Doctrine Grounding (JP 3-12 / JP 5-0)", _bullet_list(doctrine_notes))

            with col_strat:
                if strategic_notes:
                    _card("Strategic Assessment (CSIS)", _bullet_list(strategic_notes))

            if infra_records:
                infra_rows = "".join(
                    f"""<tr>
                        <td>{r.get('name', '—')}</td>
                        <td style="color:#b8c8d8">{r.get('type', '—').replace('_', ' ').title()}</td>
                        <td>{r.get('location', '—')}</td>
                        <td>{'<span class="chip chip-red">CRITICAL</span>' if r.get('criticality') == 'critical' else '<span class="chip chip-amber">HIGH</span>' if r.get('criticality') == 'high' else '<span class="chip chip-white">MED</span>'}</td>
                        <td style="color:#7a9ab8;font-size:0.75rem">{r.get('risk_label', '')[:80]}</td>
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

            if recent_events:
                event_rows = "".join(
                    f"""<tr>
                        <td style="color:#6a8aa0;font-size:0.75rem">{ev.get('timestamp','')[:10] or '—'}</td>
                        <td style="color:#b8c8d8;font-size:0.75rem;text-transform:uppercase">{ev.get('source','—')}</td>
                        <td style="color:#8aa0b4;font-size:0.75rem">{ev.get('location','—')}</td>
                        <td style="font-size:0.75rem;color:#b8c8d8">{ev.get('summary','—')[:120]}</td>
                    </tr>"""
                    for ev in recent_events[:6]
                )
                events_table = f"""
                <table class="gm-table">
                    <thead><tr><th>Date</th><th>Source</th><th>Location</th><th>Signal</th></tr></thead>
                    <tbody>{event_rows}</tbody>
                </table>"""
                _card("Recent Intelligence Signals (GDELT / Local Conflict)", events_table)

        # ── Live Intel expander (Live / Historical / Terrain) ─────────────────
        with st.expander("🛰  Live Intel — GDELT · LiveUAMap · UCDP · GTD · OpenTopography", expanded=False):
            _default_region = scenario.get("name") or scenario.get("query") or ""
            _intel_region = st.text_input(
                "Region (free text — e.g. 'Ukraine', 'Taiwan Strait', 'Sahel')",
                value=_default_region,
                key="intel_region_input",
            )
            _live_tab, _hist_tab, _terr_tab = st.tabs(
                ["Live events", "Historical baseline", "Terrain & infrastructure"]
            )

            with _live_tab:
                _payload = _get(
                    f"/events/live?region={_intel_region}&hours=24&limit=20",
                    API_URL,
                ) or {}
                _events = _payload.get("events") or []
                if not _events:
                    st.markdown(
                        '<div class="gm-dim-note">No live events for this region in the last 24h.</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    def _tw_chip(tw: float) -> str:
                        if tw >= 0.66:
                            return f'<span class="chip chip-red">{tw:.2f}</span>'
                        if tw >= 0.33:
                            return f'<span class="chip chip-amber">{tw:.2f}</span>'
                        return f'<span class="chip chip-green">{tw:.2f}</span>'

                    _rows = "".join(
                        f"""<tr>
                            <td style="font-size:0.74rem;text-transform:uppercase;color:#90b8d4">{ev.get('source','—')}</td>
                            <td style="font-size:0.74rem;color:#6a8aa0">{(ev.get('timestamp','') or '')[:16]}</td>
                            <td style="font-size:0.78rem">{(ev.get('location','—') or '—')[:40]}</td>
                            <td style="font-size:0.78rem;color:#b8c8d8">{(ev.get('summary','—') or '—')[:140]}</td>
                            <td>{_tw_chip(float(ev.get('tension_weight') or 0))}</td>
                        </tr>"""
                        for ev in _events
                    )
                    st.markdown(
                        f"""<table class="gm-table">
                            <colgroup>
                                <col style="width:11%">
                                <col style="width:14%">
                                <col style="width:18%">
                                <col style="width:48%">
                                <col style="width:9%">
                            </colgroup>
                            <thead><tr><th>Source</th><th>Time (UTC)</th><th>Location</th><th>Summary</th><th>Tension</th></tr></thead>
                            <tbody>{_rows}</tbody>
                        </table>""",
                        unsafe_allow_html=True,
                    )

            with _hist_tab:
                _hist_payload = _get(
                    f"/history/gtd?region={_intel_region}&limit=20",
                    API_URL,
                ) or {}
                _hist_events = _hist_payload.get("events") or []
                if not _hist_events:
                    st.markdown(
                        '<div class="gm-dim-note">No GTD baseline records matched this region.</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    _rows = "".join(
                        f"""<tr>
                            <td style="font-size:0.74rem;color:#90b8d4">{(ev.get('timestamp','') or '')[:10]}</td>
                            <td style="font-size:0.78rem;color:#c8daea">{(ev.get('location','—') or '—')[:36]}</td>
                            <td style="font-size:0.78rem;text-transform:uppercase;color:#7a9ab8">{(ev.get('event_type','—') or '—')[:24]}</td>
                            <td style="font-size:0.78rem;color:#b8c8d8">{(ev.get('summary','—') or '—')[:160]}</td>
                        </tr>"""
                        for ev in _hist_events
                    )
                    st.markdown(
                        f"""<table class="gm-table">
                            <colgroup><col style="width:11%"><col style="width:22%"><col style="width:17%"><col style="width:50%"></colgroup>
                            <thead><tr><th>Year</th><th>Location</th><th>Type</th><th>Summary</th></tr></thead>
                            <tbody>{_rows}</tbody>
                        </table>""",
                        unsafe_allow_html=True,
                    )

            with _terr_tab:
                _terrain_payload = _get(
                    f"/terrain?region={_intel_region}",
                    API_URL,
                ) or {}
                _summary = _terrain_payload.get("summary") or {}
                if not _summary:
                    st.markdown(
                        '<div class="gm-dim-note">No terrain summary for this region (set OPENTOPO_API_KEY for live SRTM queries).</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    _terrain_rows = (
                        _kv_row("Min Elevation",  f'{_summary.get("min_elev_m", 0)} m')
                        + _kv_row("Mean Elevation", f'{_summary.get("mean_elev_m", 0)} m')
                        + _kv_row("Max Elevation",  f'{_summary.get("max_elev_m", 0)} m')
                        + _kv_row("Terrain Class",
                                  f'<span class="chip chip-teal">'
                                  f'{(_summary.get("terrain_class","—") or "—").upper()}</span>')
                    )
                    st.markdown(_terrain_rows, unsafe_allow_html=True)

                # OSM infrastructure context (already attached to scenario)
                if infra_records:
                    st.markdown(
                        '<div class="gm-sub-header" style="margin-top:14px">Top OSM Infrastructure</div>',
                        unsafe_allow_html=True,
                    )
                    _osm_rows = "".join(
                        f"""<tr>
                            <td style="font-size:0.78rem;color:#c8daea">{r.get('name','—')[:40]}</td>
                            <td style="font-size:0.74rem;color:#7a9ab8;text-transform:uppercase">{(r.get('type','—') or '—').replace('_',' ')}</td>
                            <td style="font-size:0.74rem;color:#90b8d4">{(r.get('location','—') or '—')[:32]}</td>
                        </tr>"""
                        for r in infra_records[:8]
                    )
                    st.markdown(
                        f"""<table class="gm-table">
                            <thead><tr><th>Facility</th><th>Type</th><th>Location</th></tr></thead>
                            <tbody>{_osm_rows}</tbody>
                        </table>""",
                        unsafe_allow_html=True,
                    )


# ── Tab 2: Move ───────────────────────────────────────────────────────────────
elif _active_tab == "MOVE":
    st.markdown('<div class="gm-section-label" style="margin-bottom:8px">Submit Blue Move</div>', unsafe_allow_html=True)
    st.markdown('<div class="gm-body" style="margin-bottom:14px">Describe your cyber defensive action in plain English. The engine will parse, adjudicate, and generate a Red counter-move.</div>', unsafe_allow_html=True)

    blue_move = st.text_area(
        "Blue move",
        height=120,
        placeholder="e.g. Isolate the SCADA HMI from the corporate VLAN and hunt for persistence on the jump host",
        label_visibility="collapsed",
    )

    if st.button("Execute Move", use_container_width=True, type="primary"):
        if not blue_move.strip():
            st.warning("Enter a move first.")
        else:
            with st.spinner("Adjudicating…"):
                result = _post("/turn", {"blue_move": blue_move}, API_URL)
            if result:
                st.session_state["last_result"] = result
                st.success(f"Turn {result['turn_id']} recorded — switch to Result or AAR.")

    if st.session_state["last_result"]:
        lr = st.session_state["last_result"]
        p   = lr["parsed"]
        adj = lr["adjudication"]
        red = lr["red"]

        move_html = format_parsed_move(p)
        _card(f"Move Review — Turn {lr['turn_id']}", move_html)

        assumptions = p.get("assumptions", [])
        if assumptions:
            with st.expander("Analyst Assumptions"):
                st.markdown(_bullet_list([_na(a) for a in assumptions]), unsafe_allow_html=True)


# ── Tab 3: Result ─────────────────────────────────────────────────────────────
elif _active_tab == "RESULT":
    lr = st.session_state["last_result"]
    if not lr:
        st.markdown('<div class="gm-body" style="padding:24px 0">Submit a Blue move to see results.</div>', unsafe_allow_html=True)
    else:
        p   = lr["parsed"]
        adj = lr["adjudication"]
        red = lr["red"]
        summary = format_result_move_summary(p, adj, red)

        st.markdown(f"""
        <div class="gm-mission-header">
            <div>
                <div class="gm-mission-eyebrow">Turn {lr['turn_id']} — Result</div>
                <div class="gm-mission-title">
                    <span class="gm-value">{summary['action']}</span>
                    <span style="color:#3a5a7a;margin:0 8px;font-size:0.9rem">→</span>
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
            _card("Red Cell Response", red_html, featured=True)

            with st.expander("Red Team Rationale"):
                st.markdown(f'<div class="gm-body">{_na(red.get("rationale"))}</div>', unsafe_allow_html=True)

        # ── Doctrine references (JCS / CSIS / MITRE) ──────────────────────────
        _result_aar = lr.get("aar") or {}
        _result_cites = _result_aar.get("citations") or []
        if _result_cites:
            with st.expander(f"📚 Doctrine references ({len(_result_cites)})"):
                _doc_html = "".join(
                    f'<div style="padding:8px 0;border-bottom:1px solid #161e2a;font-size:0.80rem">'
                    f'<strong style="color:#6a9ab8">{_na(c.get("source"))}</strong>'
                    f' <span style="color:#3e5060">·</span>'
                    f' <span style="color:#6a8aa0">{_na(c.get("text",""))[:200]}…</span></div>'
                    for c in _result_cites[:5]
                )
                st.markdown(_doc_html, unsafe_allow_html=True)


# ── Tab 4: AAR ────────────────────────────────────────────────────────────────
elif _active_tab == "AAR":
    lr = st.session_state["last_result"]
    if not lr or not lr.get("aar"):
        st.markdown('<div class="gm-body" style="padding:24px 0">Submit a Blue move to generate the After-Action Review.</div>', unsafe_allow_html=True)
    else:
        aar = lr["aar"]
        p   = lr["parsed"]

        st.markdown(f"""
        <div class="gm-mission-header">
            <div>
                <div class="gm-mission-eyebrow">After-Action Review</div>
                <div class="gm-mission-title">Turn {lr['turn_id']} — {_na(p.get('action')).title()}</div>
            </div>
            <span class="chip chip-teal">✓ AAR COMPLETE</span>
        </div>
        """, unsafe_allow_html=True)

        ui_text = format_aar(aar)
        if ui_text:
            _card("Executive Debrief", f'<div class="gm-body" style="line-height:1.75">{ui_text}</div>', featured=True)
        else:
            st.markdown('<div class="gm-body">AAR text not available for this turn.</div>', unsafe_allow_html=True)

        citations = aar.get("citations") or []
        if citations:
            cite_html = "".join(
                f'<div style="padding:8px 0;border-bottom:1px solid #161e2a;font-size:0.80rem">'
                f'<strong style="color:#6a9ab8">{_na(c.get("source"))}</strong>'
                f' <span style="color:#3e5060">·</span>'
                f' <span style="color:#6a8aa0">{_na(c.get("text",""))[:160]}…</span></div>'
                for c in citations[:5]
            )
            with st.expander(f"📚 Doctrine references ({len(citations)})"):
                st.markdown(cite_html, unsafe_allow_html=True)


# ── Tab 5: Timeline ───────────────────────────────────────────────────────────
elif _active_tab == "TIMELINE":
    st.markdown('<div class="gm-section-label" style="margin-bottom:14px">Operational Turn Log</div>', unsafe_allow_html=True)
    history: Optional[List[Dict[str, Any]]] = _get("/history", API_URL)

    if not history:
        st.markdown('<div class="gm-body" style="padding:24px 0">No turns yet. Submit a Blue move to start.</div>', unsafe_allow_html=True)
    else:
        for turn in reversed(history):
            entry = format_timeline_entry(turn)
            label = f"Turn {entry['turn_id']}  ·  {entry['action_label'].upper()} → {entry['target_label'].upper()}  ·  {entry['success_pct']}"

            with st.expander(label):
                h1, h2, h3 = st.columns(3)

                with h1:
                    blue_html = f'<div class="gm-body" style="margin-bottom:12px">{entry["blue_move"]}</div>'
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
                        + _inline_collapsible("Assessment Rationale", entry["rationale"])
                    )
                    _card("Outcome", adj_body)

                with h3:
                    red_body = (
                        _kv_row("Red Response Level", entry["esc_chip"])
                        + _section_divider("Red Team Action")
                        + f'<div class="gm-body" style="margin-bottom:6px">{entry["red_action"]}</div>'
                        + _inline_collapsible("Red Team Rationale", entry["red_rationale"])
                    )
                    _card("Red Cell Response", red_body, featured=True)

                try:
                    aar_r = requests.get(f"{API_URL}/aar/{turn['turn_id']}", timeout=5)
                    if aar_r.ok:
                        aar_data = aar_r.json().get("aar", {})
                        aar_text = format_aar(aar_data)
                        if aar_text:
                            cites = aar_data.get("citations") or []
                            cite_html = ""
                            if cites:
                                cite_html = _inline_collapsible(
                                    f"📚 Doctrine references ({len(cites)})",
                                    "".join(
                                        f'<div style="padding:5px 0;border-bottom:1px solid #161e2a;font-size:0.78rem">'
                                        f'<strong style="color:#6a9ab8">{_na(c.get("source"))}</strong>'
                                        f' <span style="color:#3e5060">·</span>'
                                        f' <span style="color:#6a8aa0">{_na(c.get("text",""))[:130]}…</span></div>'
                                        for c in cites[:3]
                                    )
                                )
                            _card("After-Action Review",
                                  f'<div class="gm-body" style="line-height:1.7">{aar_text}</div>{cite_html}')
                except Exception:
                    pass
