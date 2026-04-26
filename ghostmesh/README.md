# GhostMesh

**AI-powered cyber wargaming engine.** Submit English-language cyber moves, get probabilistic adjudication, adaptive adversary responses, and doctrine-grounded after-action reviews — all running locally in under 2 seconds per turn.

Built for the SCSP Hackathon. Designed for operators, analysts, and wargame designers who need fast, credible, explainable cyber decision support.

---

## Architecture

```
English move
     │
     ▼
┌──────────┐   ┌──────────────┐   ┌──────────────────────────┐
│  Parser  │──▶│ Adjudicator  │◀──│   Retrieval (Chroma)     │
└──────────┘   └──────┬───────┘   │  TF-IDF fallback         │
                       │           └──────────────────────────┘
                       ▼                        ▲
               ┌──────────────┐                │
               │   Red Cell   │────────────────┘
               │ state machine│
               └──────┬───────┘
                       │
                       ▼
                ┌─────────────┐
                │     AAR     │◀── Retrieval citations
                └──────┬──────┘
                       │
                       ▼
                ┌─────────────┐
                │   SQLite    │
                └──────┬──────┘
                       │
                       ▼
                ┌─────────────┐
                │  Streamlit  │
                └─────────────┘
```

### Module map

| Module | File | Purpose |
|--------|------|---------|
| Parser | `backend/parser.py` | NL → structured intent (keyword, no LLM) |
| Adjudicator | `backend/adjudicator.py` | Probabilistic outcome + doctrine note |
| Red Cell | `backend/redcell.py` | Adaptive adversary state machine |
| AAR | `backend/aar.py` | Deterministic debrief + retrieval citations |
| Retrieval | `retrieval/service.py` | Chroma semantic / TF-IDF fallback |
| Scenario Seeder | `scenarios/seeder.py` | Canned + GDELT-seeded scenarios |
| DB | `backend/db.py` | SQLite turns, AARs, scenarios |
| API | `backend/main.py` | FastAPI REST |
| UI | `frontend/app.py` | Streamlit tabbed interface |

---

## Datasets & APIs

| Source | Usage | Auth |
|--------|-------|------|
| MITRE ATT&CK for ICS | Corpus excerpts in `retrieval/corpus/` — T0801–T0867 technique stubs | None (public) |
| CISA Advisories (AA23-144A) | Volt Typhoon / APT profile corpus | None (public) |
| ESET Research (Industroyer) | Sandworm corpus | None (public) |
| NSA/CISA LOTL Advisory | Defensive pattern corpus | None (public) |
| GDELT Doc 2.0 | Real-time news → scenario seeding | None (no API key) |

All corpus files ship under `retrieval/corpus/*.md`. Runs fully offline — GDELT is optional (falls back to canned scenarios automatically).

---

## Quick Start

**Requires Python 3.10+**

```bash
cd ghostmesh
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# One-time: build vector store from corpus
python -m retrieval.ingest

# Terminal 1 — API (port 8029)
uvicorn backend.main:app --reload --port 8029

# Terminal 2 — UI (port 8501)
streamlit run frontend/app.py
```

- UI: http://localhost:8501
- API docs: http://localhost:8029/docs

### Smoke test

```bash
# Active scenario
curl http://localhost:8029/scenario | python3 -m json.tool

# Submit a Blue move
curl -s -X POST http://localhost:8029/turn \
  -H 'content-type: application/json' \
  -d '{"blue_move":"Isolate the SCADA HMI and hunt for persistence on the jump host"}' \
  | python3 -m json.tool

# List all scenarios
curl http://localhost:8029/scenarios | python3 -m json.tool

# Seed from news (requires internet)
curl -s -X POST http://localhost:8029/scenarios/seed \
  -H 'content-type: application/json' \
  -d '{"query":"Volt Typhoon substation","use_api":true}' \
  | python3 -m json.tool

# Reset demo
curl -X POST http://localhost:8029/reset
```

---

## Canned Scenarios

| ID | Name | Threat |
|----|------|--------|
| `tidewatch-001` | Operation Tidewatch | Nation-state APT in power utility SCADA (default) |
| `port-cyber-001` | Operation Tidegate | IRGC-class actor in container port terminal |
| `grid-substation-001` | Operation Ironwood | Volt Typhoon LOTL in substation OT |
| `telecom-bgp-001` | Operation Phantom Route | DPRK BGP hijack at Tier-1 ISP |

Switch scenarios via the sidebar picker in the UI, or `POST /scenarios/select`.

---

## Full directory tree

```
ghostmesh/
├── backend/
│   ├── main.py          FastAPI routes (turns, scenarios, history, reset)
│   ├── db.py            SQLite persistence (turns, aars, scenarios tables)
│   ├── scenario.py      Shim → scenarios/seeder.py
│   ├── parser.py        NL → structured move intent
│   ├── adjudicator.py   Seeded probabilistic outcome + doctrine note
│   ├── redcell.py       State-machine adversary engine
│   ├── aar.py           Deterministic AAR + retrieval citations
│   └── schemas.py       Pydantic models (shared contracts)
├── retrieval/
│   ├── ingest.py        Corpus → Chroma (CLI, idempotent)
│   ├── service.py       retrieve() — Chroma primary, TF-IDF fallback
│   ├── fallback.py      Pure-python TF-IDF (no deps)
│   └── corpus/          18 markdown files (MITRE, APT, defense, concepts)
├── scenarios/
│   ├── seeder.py        Scenario resolution + seed_from_api
│   ├── gdelt.py         GDELT Doc 2.0 client
│   ├── mapping.py       GDELT articles → Scenario
│   └── canned/          4 scenario JSONs
├── frontend/
│   └── app.py           Streamlit (tabs: Brief / Move / Result / AAR / Timeline)
├── docs/
│   ├── DEMO_SCRIPT.md   5-minute click flow + narration
│   ├── JUDGE_TALKING_POINTS.md
│   └── ARCHITECTURE.md
├── data/                Runtime artifacts (gitignored)
│   ├── ghostmesh.db
│   └── chroma/
└── requirements.txt
```

---

## Troubleshooting

**Chroma cold-start** — run `python -m retrieval.ingest` once before the demo. Warmup is called on API startup but ingest must run first.

**GDELT timeout** — offline expected. Falls back to `tidewatch-001` within 4s.

**Port collision** — change `--port 8029` and update the API URL in the Streamlit sidebar.

**`chromadb` not installed** — TF-IDF fallback activates automatically. Retrieval still works.

**`ModuleNotFoundError: retrieval`** — run all commands from the `ghostmesh/` directory.
