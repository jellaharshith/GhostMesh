# GhostMesh — 5-Minute Demo Script

## Setup (before judges arrive)

```bash
cd ghostmesh
source .venv/bin/activate
python -m retrieval.ingest          # one-time, pre-warm chroma
uvicorn backend.main:app --port 8029 &
streamlit run frontend/app.py
```

Open http://localhost:8501 in a browser. Verify the API URL shows `http://localhost:8029` in the sidebar.

---

## Demo Flow

### 0:00–0:30 — Brief panel: set the scene

**Click:** "📋 Brief" tab (default)

**Say:**
> "GhostMesh is a cyber wargaming engine. This is Operation Tidewatch — a real-world-style scenario where a nation-state APT has pre-positioned inside a power utility's OT network, one step from ICS impact. The Blue Team has to evict them before Stage 7."

**Show:** Scenario name, brief summary, Blue objectives (grid uptime, eviction, attribution), Red posture (persistence on jump host, staging toward HMI), and asset status icons (HMI-01 at-risk, HIS-01 compromised, JH-01 compromised).

---

### 0:30–1:00 — (Optional) Seed from news

**Click:** Sidebar "🔍 Seed from news…" expander

**Type:** `Volt Typhoon substation United States`

**Click:** "🌐 Seed scenario"

**Say:**
> "We can also pull live scenarios from GDELT — a global news event database. GhostMesh maps recent geopolitical cyber events into a playable scenario automatically. If the API is down, it falls back to a canned scenario."

**Show:** New scenario appears. Switch back to Tidewatch via the dropdown for the main demo.

---

### 1:00–1:30 — Submit a Blue move

**Click:** "🔵 Move" tab

**Type:**
> `Isolate the SCADA HMI from the corporate VLAN and hunt for persistence on the jump host`

**Click:** "▶ Execute Move"

**Say:**
> "Blue Team submits moves in plain English. The parser extracts structured intent — action, target, stealth level, risk posture, confidence. No LLM in the hot path — this is deterministic and fast."

---

### 1:30–3:00 — Walk through the Result panel

**Click:** "⚖️ Result" tab

**Say:**
> "The adjudicator uses a seeded probabilistic model — not binary win/lose. Every outcome is partial. You get success probability, detection risk, attribution risk."

**Show:**
- Progress bars for success probability (green/yellow/red by band), detection risk, attribution risk
- Effects list (what actually happened)
- **Cascading Effects** section — show horizon labels: ⚡ immediate, ⏱ next-turn, 📅 medium-term
- Red Cell column: escalation level with color icon (🟠 escalate means adversary is advancing)

**Say:**
> "The Red Cell is a state machine — it tracks adversary pressure, remaining footholds, urgency across turns. It doesn't just react to this move; it uses the full game history to determine posture. Here you can see it escalated because pressure is low and it still has 4 footholds."

---

### 3:00–4:00 — After-Action Review

**Click:** "📊 AAR" tab

**Say:**
> "The After-Action Review is the intelligence product. What happened, why it happened, key risks, cascading effects, and a recommended next move. All deterministic — no LLM."

**Show:**
- Headline (e.g. "Partial `isolate` on `HMI-01` — Red escalate")
- What happened / Why it happened bullets
- Key risks (red/yellow/green severity)
- Recommended next move
- "📚 Sources" expander → click it

**Say:**
> "These citations come from a local vector store built from MITRE ATT&CK for ICS, CISA advisories, and APT research. The system retrieves relevant doctrine and grounds its explanation in real-world references. This is where the retrieval layer pays off for credibility."

---

### 4:00–5:00 — Second turn + Timeline

**Click:** "🔵 Move" tab again

**Type:**
> `Rotate credentials on the jump host and deploy EDR sensors on the historian`

**Click:** "▶ Execute Move"

**Click:** "📜 Timeline" tab

**Say:**
> "Two turns in, you can see the state evolving. Red Cell changed posture based on the credential rotation — it shifts to `hold` because its stolen creds were invalidated. The timeline shows the full game history: action, target, outcome, escalation level for each turn."

**Show:** Two expanders in the timeline, each with parsed/adjudication/red JSON and AAR ui_text.

---

## Reset between runs

**Click sidebar:** "🔄 Reset Game" — clears turn history, keeps scenarios.

---

## Key numbers to cite

- Turn latency: ~200ms (no LLM in hot path)
- Corpus: 19 doctrine files, 57 indexed chunks
- Scenario seeding: GDELT query → playable scenario in <4s
- Canned scenarios: 4 (power grid, port, substation, BGP)
- Red Cell postures: 4 (aggressive, opportunistic, conservative, desperate)
- Response playbook: 48 variants (12 action classes × 4 tiers)
