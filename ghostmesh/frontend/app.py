"""GhostMesh — Streamlit frontend"""
from __future__ import annotations
import json
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

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🕸️ GhostMesh")
    st.caption("AI Cyber Wargaming Engine")
    st.divider()
    api_url = st.text_input("API base URL", value="http://localhost:8029")
    st.divider()
    if st.button("🔄 Reset Game (clear history)", use_container_width=True):
        try:
            r = requests.post(f"{api_url}/reset", timeout=5)
            if r.ok:
                st.success("History cleared.")
                st.rerun()
            else:
                st.error(f"Reset failed: {r.text}")
        except Exception as e:
            st.error(str(e))
    st.divider()
    st.caption("Blue Team interface — submit moves in plain English.")


# ── Helpers ───────────────────────────────────────────────────────────────────
def _get(path: str) -> Optional[Any]:
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


def _post(path: str, payload: Dict[str, Any]) -> Optional[Any]:
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


def _pct(v: float) -> str:
    return f"{v * 100:.0f}%"


def _color_pct(v: float) -> str:
    if v >= 0.75:
        return "🟢"
    if v >= 0.45:
        return "🟡"
    return "🔴"


ESCALATION_COLOR = {
    "retreat":             "🟢",
    "hold":                "🟡",
    "escalate":            "🟠",
    "escalate_destructive":"🔴",
}


# ── Scenario panel ────────────────────────────────────────────────────────────
scenario = _get("/scenario")

if scenario:
    st.header(f"📋 {scenario['name']}")
    st.markdown(f"> {scenario['brief']}")

    col_obj, col_red, col_assets = st.columns([2, 2, 3])
    with col_obj:
        st.subheader("Blue Objectives")
        for obj in scenario["blue_objectives"]:
            st.markdown(f"- {obj}")
    with col_red:
        st.subheader("Red Posture")
        st.markdown(scenario["red_posture"])
    with col_assets:
        st.subheader("Assets")
        STATUS_ICON = {"at-risk": "⚠️", "compromised": "🔴", "clean": "✅",
                       "online": "🟢", "patching-pending": "🟡"}
        for asset in scenario["assets"]:
            icon = STATUS_ICON.get(asset["status"], "❓")
            st.markdown(f"{icon} **{asset['name']}** — {asset['type']} `{asset['status']}`")

st.divider()

# ── Blue move input ───────────────────────────────────────────────────────────
st.subheader("🔵 Submit Blue Move")
with st.form("blue_move_form"):
    blue_move = st.text_area(
        "Describe your cyber move in plain English",
        height=100,
        placeholder="e.g. Isolate the SCADA HMI from the corporate VLAN and hunt for persistence on the jump host",
    )
    submitted = st.form_submit_button("▶ Execute Move", use_container_width=True)

if submitted:
    if not blue_move.strip():
        st.warning("Enter a move first.")
    else:
        with st.spinner("Adjudicating…"):
            result = _post("/turn", {"blue_move": blue_move})

        if result:
            st.success(f"Turn {result['turn_id']} recorded  •  {result['ts']}")
            st.divider()

            # ── Three-column result ────────────────────────────────────────
            c1, c2, c3 = st.columns(3)

            # Parsed move
            with c1:
                st.subheader("🔍 Parsed Intent")
                p = result["parsed"]
                st.markdown(f"**Action:** `{p['action']}`")
                st.markdown(f"**Target:** `{p['target']}`")
                st.markdown(f"**Intent:** {p['intent']}")
                st.markdown(f"**Technique:** `{p['technique_family']}`")
                st.markdown(f"**Stealth:** `{p['stealth_level']}`  |  **Risk:** `{p['risk']}`")
                st.markdown(f"**Time horizon:** {p['time_horizon']}")
                st.markdown(f"**Confidence:** {_color_pct(p['confidence'])} {_pct(p['confidence'])}")
                with st.expander("Assumptions"):
                    for a in p["assumptions"]:
                        st.markdown(f"- {a}")

            # Adjudication
            with c2:
                st.subheader("⚖️ Adjudication")
                adj = result["adjudication"]
                sp = adj["success_probability"]
                dr = adj["detection_risk"]
                ar = adj["attribution_risk"]
                st.metric("Success probability", _pct(sp),
                          delta=None, help="Probabilistic outcome — not binary")
                mcol1, mcol2 = st.columns(2)
                mcol1.metric("Detection risk", _pct(dr))
                mcol2.metric("Attribution risk", _pct(ar))

                st.markdown("**Effects:**")
                for e in adj["effects"]:
                    st.markdown(f"- {e}")
                st.markdown("**Cascading effects:**")
                for ce in adj["cascading_effects"]:
                    st.markdown(f"- {ce}")
                with st.expander("Rationale"):
                    st.write(adj["rationale"])

            # Red response
            with c3:
                st.subheader("🔴 Red Cell Response")
                red = result["red"]
                esc = red["escalation_level"]
                esc_icon = ESCALATION_COLOR.get(esc, "❓")
                st.markdown(f"**Escalation:** {esc_icon} `{esc}`")
                st.markdown(f"**Action:** {red['red_action']}")
                st.markdown(f"**Target:** `{red['target']}`")
                st.markdown(f"**Intent:** {red['intent']}")
                with st.expander("Red rationale"):
                    st.write(red["rationale"])

            # ── After-Action Review ────────────────────────────────────────
            if result.get("aar"):
                st.divider()
                aar = result["aar"]
                st.markdown(aar["ui_text"])
                with st.expander("AAR — full JSON"):
                    st.json(aar)

            st.divider()

# ── Turn history ──────────────────────────────────────────────────────────────
st.subheader("📜 Turn History")
history: Optional[List[Dict[str, Any]]] = _get("/history")

if not history:
    st.info("No turns yet. Submit a Blue move above.")
else:
    for turn in reversed(history):
        p = turn["parsed"]
        adj = turn["adjudication"]
        red = turn["red"]
        esc = red["escalation_level"]
        esc_icon = ESCALATION_COLOR.get(esc, "❓")

        label = (
            f"Turn {turn['turn_id']}  |  "
            f"`{p['action']}` → `{p['target']}`  |  "
            f"Success {_pct(adj['success_probability'])}  |  "
            f"Red: {esc_icon} {esc}"
        )
        with st.expander(label):
            h1, h2, h3 = st.columns(3)
            with h1:
                st.markdown(f"**Blue move:** {turn['blue_move']}")
                st.json(p)
            with h2:
                st.json(adj)
            with h3:
                st.json(red)
            # Fetch and render AAR for this turn
            try:
                aar_r = requests.get(f"{api_url}/aar/{turn['turn_id']}", timeout=5)
                if aar_r.ok:
                    st.markdown(aar_r.json()["aar"]["ui_text"])
            except Exception:
                pass
