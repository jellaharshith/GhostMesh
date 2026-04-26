# GhostMesh — Judge Talking Points

## What is GhostMesh?

A local-first AI cyber wargaming engine that lets analysts submit plain-English defensive moves against adaptive adversary scenarios and receive probabilistic, doctrine-grounded outcomes with full explainability. Every decision is backed by a traceable rationale and real-world source citations.

---

## Novelty

**Problem it solves:** Existing cyber wargaming tools are either too slow (multi-day tabletops), too opaque (LLM black boxes), or require classified systems. GhostMesh is fast, local, explainable, and runs on a laptop.

**Novel combination:**
- Deterministic probabilistic adjudication (seeded RNG, reproducible outcomes) — not binary win/lose
- Adaptive state-machine adversary that replays full game history to compute pressure, footholds, and urgency — adversary behavior evolves across turns
- Retrieval-grounded explainability — every AAR cites real MITRE ATT&CK for ICS techniques and CISA advisories
- Real-world scenario seeding from GDELT (global news → playable scenario in <4s)
- Graceful degradation at every layer (no internet → canned scenarios; no Chroma → TF-IDF; no LLM → deterministic)

---

## Technical Difficulty

**6 interlocking modules with coherent contracts:**

| Module | Technical challenge |
|--------|-------------------|
| Parser | NL → structured intent without LLM; 11 action classes, confidence scoring |
| Adjudicator | Composited probabilistic model: effectiveness × execution × preparation × target-fit; conditional P(attribution\|detection) |
| Red Cell | State-machine with pressure accumulation, foothold tracking, recency decay, doctrine bias table (48 playbook variants), escalation tier logic |
| AAR | Deterministic debrief from effect tags + cascade projection + recommendation lookup table (4×4) |
| Retrieval | Chroma vector store + pure-python TF-IDF fallback; lazy-load, timeout-guarded, never raises |
| Scenario Seeder | GDELT API → keyword projection → normalized scenario with infra and actor heuristics; deterministic ID from content hash |

**Architecture decisions:**
- No LLM in the hot path — sub-200ms turn latency
- Everything local-first, offline-capable
- SQLite for persistence (no setup required)
- Additive design — all hooks wrapped in try/except, graceful degradation at every failure point

---

## National Impact

**Who uses this:** Cyber operators, red team planners, wargame designers, incident response trainers, DoD/IC analysts.

**Why it matters:**
- ICS/OT cyber threats to critical infrastructure (power, water, ports, telecom) are escalating. Volt Typhoon pre-positioned in US critical infrastructure. CyberAv3ngers hit US water utilities. Sandworm destroyed Ukrainian grid.
- Decision-makers need fast, repeatable wargaming to test response playbooks without live systems.
- GhostMesh lets analysts iterate on cyber decisions against doctrine-grounded adversary models in minutes, not days.
- Training value: operators learn which actions trigger adversary escalation, what cascading effects look like, and how to read doctrine-backed rationales.

**Scalability path:** Local prototype → cloud deployment → multi-player wargaming → integration with existing exercise frameworks.

---

## Problem-Solution Fit

**Problem:** Cyber wargaming is slow, expensive, and opaque. Existing tools either require classified infrastructure, cost millions, or produce outputs that can't be explained to non-technical stakeholders.

**Solution:** GhostMesh closes the gap with:
- Speed: full turn loop in <200ms
- Accessibility: plain English input, no special training required
- Explainability: every output has a traceable rationale + doctrine citations
- Cost: runs on a laptop, no APIs, no cloud, no classified data
- Credibility: grounded in MITRE ATT&CK for ICS, CISA advisories, and real APT research

**Demo proof:** One judge with no wargaming experience can submit a move and read the AAR in under 30 seconds.
