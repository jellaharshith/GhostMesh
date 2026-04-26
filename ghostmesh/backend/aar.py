"""
After-Action Review generator: scenario + parsed + adjudication + red + history
→ structured debrief (JSON + markdown).

Deterministic, no LLM in hot path. Reuses outcome and severity tags emitted by
the adjudicator. Optional LLM polish via GHOSTMESH_LLM_AAR=1 (stub).
"""
from __future__ import annotations
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


# ── Tag parsing ───────────────────────────────────────────────────────────────

_OUTCOME_TAG = re.compile(r"\[(full|partial-strong|partial-weak|failure)\]")
_SEVERITY_TAG = re.compile(r"\[severity:(low|med|high)\]")

SEVERITY_ICON = {"high": "🔴", "med": "🟡", "low": "🟢"}
HORIZON_ICON  = {"immediate": "⚡", "next-turn": "⏱", "medium-term": "📅"}


def _classify_outcome(effects: List[str]) -> str:
    if not effects:
        return "failure"
    m = _OUTCOME_TAG.search(effects[0])
    return m.group(1) if m else "failure"


def _strip_tag(s: str) -> str:
    return re.sub(r"\[[^\]]+\]\s*", "", s).strip()


# ── Section builders ──────────────────────────────────────────────────────────

def _build_what_happened(
    parsed: Dict[str, Any],
    adj: Dict[str, Any],
    red: Dict[str, Any],
) -> List[str]:
    action = parsed.get("action", "unknown")
    target = parsed.get("target", "unknown")
    sp = adj.get("success_probability", 0.0)
    bullets = [
        f"Blue executed `{action}` on `{target}` at {sp:.0%} success probability."
    ]
    for fx in adj.get("effects", [])[:2]:
        clean = _strip_tag(fx)
        if clean:
            bullets.append(clean)
    esc = red.get("escalation_level", "unknown")
    ra  = red.get("red_action", "no response")
    bullets.append(f"Red countered with **{esc}**: {ra}.")
    return bullets[:4]


def _build_why(
    parsed: Dict[str, Any],
    adj: Dict[str, Any],
    red: Dict[str, Any],
) -> List[str]:
    why: List[str] = []
    rationale = adj.get("rationale", "")
    if rationale:
        why.append(rationale.split(". ")[0] + ".")
    stealth = parsed.get("stealth_level", "medium")
    if stealth == "low":
        why.append("Low stealth posture inflated detection risk.")
    elif stealth == "high":
        why.append("High stealth posture suppressed adversary visibility.")
    if parsed.get("confidence", 1.0) < 0.6:
        why.append("Parser confidence was low — assumptions may have skewed adjudication.")
    red_rat = red.get("rationale", "")
    if red_rat:
        why.append(red_rat.split(".")[0] + ".")
    return why[:4]


def _extract_risks(
    adj: Dict[str, Any],
    red: Dict[str, Any],
    history: List[Dict[str, Any]],
    action: str,
) -> List[Dict[str, str]]:
    risks: List[Dict[str, str]] = []
    dr = adj.get("detection_risk", 0.0)
    ar = adj.get("attribution_risk", 0.0)

    if dr >= 0.60:
        risks.append({
            "label": "High detection exposure",
            "severity": "high",
            "rationale": f"Detection risk {dr:.0%} — adversary likely correlates Blue TTPs.",
        })
    elif dr >= 0.35:
        risks.append({
            "label": "Moderate detection exposure",
            "severity": "med",
            "rationale": f"Detection risk {dr:.0%}.",
        })

    if ar >= 0.40:
        risks.append({
            "label": "Attribution surface opened",
            "severity": "high",
            "rationale": f"Attribution risk {ar:.0%} — diplomatic/legal exposure.",
        })

    if red.get("escalation_level") == "escalate_destructive":
        risks.append({
            "label": "Adversary destructive escalation",
            "severity": "high",
            "rationale": "Red shifted to destructive tier — ICS impact window opening.",
        })

    # Repeat-action diminishing returns
    recent_actions = [t.get("parsed", {}).get("action") for t in history[-3:]]
    if action != "unknown" and recent_actions.count(action) >= 2:
        risks.append({
            "label": "Diminishing returns on action class",
            "severity": "med",
            "rationale": f"`{action}` repeated — adversary adapting to this playbook.",
        })

    return risks[:4]


def _project_cascades(
    cascades_in: List[str],
) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    for c in cascades_in[:4]:
        sev_match = _SEVERITY_TAG.search(c)
        sev = sev_match.group(1) if sev_match else "low"
        text = _strip_tag(c)
        lower = text.lower()
        if any(k in lower for k in ("next turn", "within 1 turn", "immediate", "re-engagement")):
            horizon = "next-turn"
        elif any(k in lower for k in ("hours", "window", "maintenance", "alert", "lock out")):
            horizon = "immediate"
        else:
            horizon = "medium-term"
        out.append({"description": text, "severity": sev, "horizon": horizon})
    return out


# ── Recommendation table ──────────────────────────────────────────────────────

_NEXT_ACTION_TABLE: Dict[Tuple[str, str], str] = {
    ("full",           "retreat"):              "Press advantage — initiate hunt on residual footholds.",
    ("full",           "hold"):                 "Lock gains — deploy monitoring on freshly-cleared assets.",
    ("full",           "escalate"):             "Counter-escalate — block alternate C2 channel before Red consolidates.",
    ("full",           "escalate_destructive"): "Evacuate HMI-01 immediately — Red is reaching for ICS impact.",
    ("partial-strong", "retreat"):              "Complete the action — re-issue against missed sub-targets.",
    ("partial-strong", "hold"):                 "Patch downstream — close residual vectors flagged in effects.",
    ("partial-strong", "escalate"):             "Rotate credentials and harden segmentation in parallel.",
    ("partial-strong", "escalate_destructive"): "Evacuate HMI-01 — protect physical layer while finishing eviction.",
    ("partial-weak",   "retreat"):              "Re-attempt with higher-confidence intel — current scope was insufficient.",
    ("partial-weak",   "hold"):                 "Pivot to hunt — confirm what the partial action actually changed.",
    ("partial-weak",   "escalate"):             "Block egress and rotate credentials before Red regains tempo.",
    ("partial-weak",   "escalate_destructive"): "Evacuate HMI-01 now — partial defense plus destructive Red equals imminent impact.",
    ("failure",        "retreat"):              "Re-plan — current approach burned. Switch action class.",
    ("failure",        "hold"):                 "Switch to deceive — buy time while diagnosing the failure.",
    ("failure",        "escalate"):             "Emergency block plus monitor — Red is advancing through the gap.",
    ("failure",        "escalate_destructive"): "Evacuate HMI-01 and notify CISA — destructive Red, failed Blue.",
}


def _recommend_next(outcome_class: str, red: Dict[str, Any]) -> str:
    key = (outcome_class, red.get("escalation_level", "hold"))
    return _NEXT_ACTION_TABLE.get(key, "Re-assess posture and resubmit a higher-confidence move.")


def _compute_confidence(success_prob: float, parser_conf: float) -> float:
    return round(min(0.99, 0.5 + 0.25 * success_prob + 0.25 * parser_conf), 2)


def _headline(outcome_class: str, action: str, target: str, esc: str) -> str:
    pretty = {
        "full":           "Decisive",
        "partial-strong": "Partial",
        "partial-weak":   "Marginal",
        "failure":        "Failed",
    }.get(outcome_class, "Unknown")
    return f"{pretty} `{action}` on `{target}` — Red {esc}."


def _render_ui_text(
    turn_id: int,
    headline: str,
    what: List[str],
    why: List[str],
    risks: List[Dict[str, str]],
    cascades: List[Dict[str, str]],
    next_action: str,
    confidence: float,
    citations: Optional[List[Dict]] = None,
    doctrine_notes: Optional[List[str]] = None,
    strategic_notes: Optional[List[str]] = None,
) -> str:
    conf_icon = "🟢" if confidence >= 0.75 else ("🟡" if confidence >= 0.50 else "🔴")
    lines = [
        f"### 📊 After-Action Review — Turn {turn_id}",
        f"**{headline}**  {conf_icon} confidence {confidence:.0%}",
        "",
        "**What happened**",
    ]
    lines += [f"- {b}" for b in what]
    lines += ["", "**Why it happened**"]
    lines += [f"- {b}" for b in why]
    lines += ["", "**Key risks**"]
    if risks:
        lines += [
            f"- {SEVERITY_ICON[r['severity']]} **{r['label']}**: {r['rationale']}"
            for r in risks
        ]
    else:
        lines.append("- 🟢 No significant risks identified.")
    lines += ["", "**Cascading effects**"]
    if cascades:
        lines += [
            f"- {HORIZON_ICON[c['horizon']]} {c['horizon']} ({SEVERITY_ICON[c['severity']]} {c['severity']}) — {c['description']}"
            for c in cascades
        ]
    else:
        lines.append("- *(none projected)*")
    lines += ["", f"**👉 Recommended next move:** {next_action}"]
    if doctrine_notes:
        lines += ["", "**Joint Doctrine Context**"]
        lines += [f"- {n}" for n in doctrine_notes[:2]]
    if strategic_notes:
        lines += ["", "**Strategic Assessment (CSIS)**"]
        lines += [f"- {n}" for n in strategic_notes[:2]]
    if citations:
        lines += ["", "**Sources**"]
        for c in citations[:3]:
            src = c.get("source", "")
            txt = c.get("text", "")[:120]
            lines.append(f"- 📄 *{src}*: {txt}…")
    return "\n".join(lines)


def _polish_aar(aar: Dict[str, Any]) -> Dict[str, Any]:
    """
    LLM-polished staff assessment in the voice of a Joint Staff J3 analyst.
    Enabled when ANTHROPIC_API_KEY is set (GHOSTMESH_LLM_AAR env var ignored).
    Adds aar["llm_debrief"] and appends a Staff Assessment section to ui_text.
    Falls back silently — deterministic AAR is always complete on its own.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        return aar

    try:
        import anthropic  # lazy import
    except ImportError:
        return aar

    # Retrieve 1-2 doctrine citations for grounding
    doctrine_ctx = ""
    try:
        from retrieval.service import retrieve
        query = f"{aar.get('outcome_class', '')} {aar.get('scenario_id', '')} doctrine"
        snips = retrieve(query, k=2, tags=["jcs", "doctrine", "concept"])
        if snips:
            doctrine_ctx = "\n".join(f"- {s['text'][:180]}" for s in snips)
    except Exception:
        pass

    what = "\n".join(f"- {b}" for b in aar.get("what_happened", []))
    why = "\n".join(f"- {b}" for b in aar.get("why_it_happened", [])[:3])
    risks = "; ".join(r.get("label", "") for r in aar.get("key_risks", []))
    nxt = aar.get("recommended_next_action", "")

    system_prompt = (
        "You are a Joint Staff J3 (Operations) analyst writing an after-action assessment "
        "for a classified cyber wargame. Write exactly 3 short paragraphs (≤60 words each): "
        "1) operational summary of what happened and why; "
        "2) key risk implications for mission success; "
        "3) recommended next action with doctrinal justification. "
        "Use precise, professional military staff language. No markdown headers. No bullet points."
    )

    user_msg = (
        f"EXERCISE: {aar.get('scenario_id', 'unknown')} | Turn {aar.get('turn_id', '?')}\n"
        f"Headline: {aar.get('headline', '')}\n"
        f"Outcome: {aar.get('outcome_class', '')}\n\n"
        f"What happened:\n{what}\n\n"
        f"Why it happened:\n{why}\n\n"
        f"Key risks: {risks or 'none identified'}\n"
        f"Recommended next move: {nxt}\n"
    )
    if doctrine_ctx:
        user_msg += f"\nDoctrine context:\n{doctrine_ctx}"
    user_msg += "\n\nWrite the 3-paragraph J3 staff assessment."

    try:
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=600,
            system=[
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": user_msg}],
        )
        debrief = msg.content[0].text.strip() if msg.content else ""
        if debrief and len(debrief) > 20:
            aar = dict(aar)
            aar["llm_debrief"] = debrief
            aar["ui_text"] = aar.get("ui_text", "") + f"\n\n**J3 Staff Assessment**\n{debrief}"
    except Exception:
        pass  # deterministic AAR is unchanged

    return aar


# ── Public entry point ────────────────────────────────────────────────────────

def generate_aar(
    turn_id: int,
    scenario: Dict[str, Any],
    parsed: Dict[str, Any],
    adjudication: Dict[str, Any],
    red: Dict[str, Any],
    history: List[Dict[str, Any]],
) -> Dict[str, Any]:
    action        = parsed.get("action", "unknown")
    outcome_class = _classify_outcome(adjudication.get("effects", []))

    what     = _build_what_happened(parsed, adjudication, red)
    why      = _build_why(parsed, adjudication, red)
    # Retrieval-grounded citations (best-effort, never raises)
    citations: list = []
    try:
        from retrieval.service import retrieve
        action_str = parsed.get("action", "unknown")
        snips = retrieve(f"{action_str} {outcome_class} doctrine", k=3, tags=["concept", "defense"])
        if snips:
            why.append(f"Doctrine note: {snips[0]['text'][:140]}")
            citations = snips
    except Exception:
        pass
    # CSIS strategic narrative enrichment (best-effort, never raises)
    try:
        from retrieval.service import retrieve as _retrieve_csis
        csis_snips = _retrieve_csis(
            f"{action} {outcome_class} strategic implications adversary",
            k=2,
            tags=["csis", "analysis"],
        )
        if csis_snips:
            why.append(f"CSIS analysis: {csis_snips[0]['text'][:160]}")
            citations = citations + csis_snips
    except Exception:
        pass
    risks    = _extract_risks(adjudication, red, history, action)
    cascades = _project_cascades(adjudication.get("cascading_effects", []))
    nxt      = _recommend_next(outcome_class, red)
    conf     = _compute_confidence(
        adjudication.get("success_probability", 0.0),
        parsed.get("confidence", 0.5),
    )
    head = _headline(
        outcome_class,
        action,
        parsed.get("target", "unknown"),
        red.get("escalation_level", "hold"),
    )
    sc_doctrine = scenario.get("doctrine_notes", [])
    sc_strategic = scenario.get("strategic_notes", [])
    ui_text = _render_ui_text(
        turn_id, head, what, why, risks, cascades, nxt, conf, citations,
        doctrine_notes=sc_doctrine, strategic_notes=sc_strategic,
    )

    aar: Dict[str, Any] = {
        "turn_id":                 turn_id,
        "scenario_id":             scenario.get("id", "unknown"),
        "headline":                head,
        "outcome_class":           outcome_class,
        "what_happened":           what,
        "why_it_happened":         why,
        "key_risks":               risks,
        "cascading_effects":       cascades,
        "recommended_next_action": nxt,
        "confidence":              conf,
        "ui_text":                 ui_text,
        "generated_ts":            datetime.now(timezone.utc).isoformat(),
        "citations":               citations,
    }
    return _polish_aar(aar)
