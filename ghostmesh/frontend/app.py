"""GhostMesh — Streamlit frontend (demo-ready)"""
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

# ── Session state ─────────────────────────────────────────────────────────────
if "last_result" not in st.session_state:
    st.session_state["last_result"] = None
if "active_scenario_id" not in st.session_state:
    st.session_state["active_scenario_id"] = None

# ── Constants ─────────────────────────────────────────────────────────────────
ESCALATION_COLOR = {
    "retreat":              "🟢",
    "hold":                 "🟡",
    "escalate":             "🟠",
    "escalate_destructive": "🔴",
}
STATUS_ICON = {
    "at-risk":         "⚠️",
    "compromised":     "🔴",
    "clean":           "✅",
    "online":          "🟢",
    "patching-pending":"🟡",
    "defaced":         "🟠",
}
SEVERITY_ICON = {"high": "🔴", "med": "🟡", "low": "🟢"}
HORIZON_ICON  = {"immediate": "⚡", "next-turn": "⏱", "medium-term": "📅"}


# ── Helpers ───────────────────────────────────────────────────────────────────
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


def _pct(v: float) -> str:
    return f"{v * 100:.0f}%"


def _risk_icon(v: float) -> str:
    if v >= 0.66:
        return "🔴"
    if v >= 0.33:
        return "🟡"
    return "🟢"


def _success_icon(v: float) -> str:
    if v >= 0.66:
        return "🟢"
    if v >= 0.33:
        return "🟡"
    return "🔴"


def _progress_row(label: str, value: float, icon_fn=None) -> None:
    icon = (icon_fn or _risk_icon)(value)
    st.markdown(f"**{icon} {label}:** {_pct(value)}")
    st.progress(value)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🕸️ GhostMesh")
    st.caption("AI Cyber Wargaming Engine")
    st.divider()

    api_url = st.text_input("API base URL", value="http://localhost:8029")
    st.divider()

    # Scenario picker
    st.markdown("**🗺️ Scenario**")
    scenarios_list: List[Dict] = _get("/scenarios", api_url) or []
    scenario_names = [s["name"] for s in scenarios_list]
    scenario_ids   = [s["id"]   for s in scenarios_list]

    current_idx = 0
    if st.session_state["active_scenario_id"] in scenario_ids:
        current_idx = scenario_ids.index(st.session_state["active_scenario_id"])

    if scenarios_list:
        chosen_name = st.selectbox("Select scenario", scenario_names, index=current_idx)
        chosen_id = scenario_ids[scenario_names.index(chosen_name)]
        if chosen_id != st.session_state.get("active_scenario_id"):
            res = _post("/scenarios/select", {"scenario_id": chosen_id}, api_url)
            if res:
                st.session_state["active_scenario_id"] = chosen_id
                st.rerun()

    with st.expander("🔍 Seed from news…"):
        seed_query = st.text_input("News query (e.g. 'Volt Typhoon substation')", key="seed_q")
        if st.button("🌐 Seed scenario", use_container_width=True):
            if seed_query.strip():
                with st.spinner("Fetching from GDELT…"):
                    seeded = _post("/scenarios/seed", {"query": seed_query, "use_api": True}, api_url)
                if seeded:
                    st.success(f"Seeded: {seeded['name']}")
                    st.rerun()
            else:
                st.warning("Enter a query first.")

    st.divider()
    if st.button("🔄 Reset Game", use_container_width=True):
        r = _post("/reset", {}, api_url)
        if r:
            st.session_state["last_result"] = None
            st.success("History cleared.")
            st.rerun()
    st.divider()
    st.caption("Blue Team interface. Plain English moves only.")


# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_brief, tab_move, tab_result, tab_aar, tab_timeline = st.tabs(
    ["📋 Brief", "🔵 Move", "⚖️ Result", "📊 AAR", "📜 Timeline"]
)


# ── Tab 1: Brief ──────────────────────────────────────────────────────────────
with tab_brief:
    scenario = _get("/scenario", api_url)
    if scenario:
        st.header(f"📋 {scenario['name']}")
        st.markdown(f"> {scenario['brief']}")
        st.divider()

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
            for asset in scenario["assets"]:
                icon = STATUS_ICON.get(asset["status"], "❓")
                st.markdown(f"{icon} **{asset['name']}** — {asset['type']} `{asset['status']}`")


# ── Tab 2: Move ───────────────────────────────────────────────────────────────
with tab_move:
    st.subheader("🔵 Submit Blue Move")
    st.caption("Describe your cyber defensive action in plain English.")

    blue_move = st.text_area(
        "Blue move",
        height=120,
        placeholder="e.g. Isolate the SCADA HMI from the corporate VLAN and hunt for persistence on the jump host",
        label_visibility="collapsed",
    )

    if st.button("▶ Execute Move", use_container_width=True, type="primary"):
        if not blue_move.strip():
            st.warning("Enter a move first.")
        else:
            with st.spinner("Adjudicating…"):
                result = _post("/turn", {"blue_move": blue_move}, api_url)
            if result:
                st.session_state["last_result"] = result
                st.success(f"Turn {result['turn_id']} recorded — switch to **Result** or **AAR** tabs.")

    if st.session_state["last_result"]:
        lr = st.session_state["last_result"]
        p = lr["parsed"]
        adj = lr["adjudication"]
        st.info(
            f"Last: Turn {lr['turn_id']} — `{p['action']}` → `{p['target']}` "
            f"| Success {_pct(adj['success_probability'])} "
            f"| Red: {ESCALATION_COLOR.get(lr['red']['escalation_level'], '❓')} {lr['red']['escalation_level']}"
        )


# ── Tab 3: Result ─────────────────────────────────────────────────────────────
with tab_result:
    lr = st.session_state["last_result"]
    if not lr:
        st.info("Submit a Blue move in the **Move** tab first.")
    else:
        st.subheader(f"Turn {lr['turn_id']} Results")
        p   = lr["parsed"]
        adj = lr["adjudication"]
        red = lr["red"]

        c1, c2, c3 = st.columns(3)

        with c1:
            st.subheader("🔍 Parsed Intent")
            st.markdown(f"**Action:** `{p['action']}`")
            st.markdown(f"**Target:** `{p['target']}`")
            st.markdown(f"**Intent:** {p['intent']}")
            st.markdown(f"**Technique:** `{p['technique_family']}`")
            st.markdown(f"**Stealth:** `{p['stealth_level']}`  |  **Risk:** `{p['risk']}`")
            st.markdown(f"**Time horizon:** {p['time_horizon']}")
            st.markdown(f"**Confidence:**")
            _progress_row("Confidence", p["confidence"], _success_icon)
            with st.expander("Assumptions"):
                for a in p.get("assumptions", []):
                    st.markdown(f"- {a}")

        with c2:
            st.subheader("⚖️ Adjudication")
            _progress_row("Success probability", adj["success_probability"], _success_icon)
            _progress_row("Detection risk", adj["detection_risk"])
            _progress_row("Attribution risk", adj["attribution_risk"])
            st.divider()
            st.markdown("**Effects:**")
            for e in adj["effects"]:
                clean_e = e.split("] ", 1)[-1] if "] " in e else e
                st.markdown(f"- {clean_e}")
            st.divider()
            st.markdown("**Cascading Effects:**")
            for ce in adj.get("cascading_effects", []):
                # ce may be a string from adjudicator or a dict from AAR
                if isinstance(ce, dict):
                    h = ce.get("horizon", "medium-term")
                    s = ce.get("severity", "low")
                    d = ce.get("description", "")
                    st.markdown(f"{HORIZON_ICON.get(h,'📅')} `{h}` {SEVERITY_ICON.get(s,'🟢')} {d}")
                else:
                    clean_ce = ce.split("] ", 1)[-1] if "] " in ce else ce
                    st.markdown(f"- {clean_ce}")
            with st.expander("Rationale"):
                st.write(adj["rationale"])

        with c3:
            st.subheader("🔴 Red Cell Response")
            esc = red["escalation_level"]
            esc_icon = ESCALATION_COLOR.get(esc, "❓")
            st.markdown(f"**Escalation:** {esc_icon} `{esc}`")
            st.markdown(f"**Action:** {red['red_action']}")
            st.markdown(f"**Target:** `{red['target']}`")
            st.markdown(f"**Intent:** {red['intent']}")
            with st.expander("Red rationale"):
                st.write(red["rationale"])


# ── Tab 4: AAR ────────────────────────────────────────────────────────────────
with tab_aar:
    lr = st.session_state["last_result"]
    if not lr or not lr.get("aar"):
        st.info("Submit a Blue move to see the After-Action Review.")
    else:
        aar = lr["aar"]
        st.markdown(aar["ui_text"])

        citations = aar.get("citations") or []
        if citations:
            with st.expander("📚 Sources"):
                for c in citations[:5]:
                    src  = c.get("source", "unknown")
                    text = c.get("text", "")[:150]
                    st.markdown(f"📄 **{src}**: {text}…")

        with st.expander("AAR — full JSON"):
            st.json(aar)


# ── Tab 5: Timeline ───────────────────────────────────────────────────────────
with tab_timeline:
    st.subheader("📜 Turn History")
    history: Optional[List[Dict[str, Any]]] = _get("/history", api_url)

    if not history:
        st.info("No turns yet. Submit a Blue move to start.")
    else:
        for turn in reversed(history):
            p   = turn["parsed"]
            adj = turn["adjudication"]
            red = turn["red"]
            esc = red["escalation_level"]
            esc_icon = ESCALATION_COLOR.get(esc, "❓")
            sp  = adj["success_probability"]
            sp_icon = _success_icon(sp)

            label = (
                f"Turn {turn['turn_id']}  |  "
                f"`{p['action']}` → `{p['target']}`  |  "
                f"{sp_icon} {_pct(sp)}  |  "
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
                try:
                    aar_r = requests.get(f"{api_url}/aar/{turn['turn_id']}", timeout=5)
                    if aar_r.ok:
                        aar_data = aar_r.json().get("aar", {})
                        st.markdown(aar_data.get("ui_text", ""))
                        cites = aar_data.get("citations") or []
                        if cites:
                            with st.expander("📚 Sources"):
                                for c in cites[:3]:
                                    st.markdown(f"📄 **{c.get('source','')}**: {c.get('text','')[:120]}…")
                except Exception:
                    pass
