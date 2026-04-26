# GhostMesh

**AI-powered cyber wargaming engine.** Type a scenario, get a live intelligence-fused threat picture, then submit English-language Blue Team moves and receive probabilistic adjudication, adaptive Red Cell responses, and doctrine-grounded after-action reviews — all running locally.

Built for the SCSP Hackathon. Designed for operators, analysts, and wargame designers who need fast, credible, explainable cyber decision support.

---

## Architecture

```
Scenario query (plain English)
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│                  Intelligence Fusion                     │
│  GDELT (news/tension) · ACLED (conflict) · UCDP (wars)  │
│  Overpass/OSM (infrastructure) · Chroma (JP 3-12 docs)  │
└─────────────────────────┬───────────────────────────────┘
                           │ FusedScenario
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
                │     AAR     │◀── JP 3-12 / CSIS citations
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

| Module          | File                          | Purpose                                             |
| --------------- | ----------------------------- | --------------------------------------------------- |
| Parser          | `backend/parser.py`           | NL → structured intent (keyword, no LLM)            |
| Adjudicator     | `backend/adjudicator.py`      | Probabilistic outcome + doctrine note               |
| Red Cell        | `backend/redcell.py`          | Adaptive adversary state machine                    |
| AAR             | `backend/aar.py`              | Deterministic debrief + JP 3-12 / CSIS citations    |
| Retrieval       | `retrieval/service.py`        | Chroma semantic / TF-IDF fallback                   |
| Scenario Seeder | `scenarios/seeder.py`         | OSINT fusion: GDELT + ACLED + UCDP + OSM            |
| Mapping         | `scenarios/mapping.py`        | Events → FusedScenario with scores + doctrine notes |
| GDELT           | `sources/gdelt_adapter.py`    | Live news tension signals                           |
| ACLED           | `sources/acled_adapter.py`    | Conflict events (seed fallback)                     |
| UCDP            | `sources/ucdp_adapter.py`     | Armed conflict history (UCDP GED API / seed)        |
| Overpass        | `sources/overpass_adapter.py` | OSM infrastructure (bbox from region text)          |
| DB              | `backend/db.py`               | SQLite turns, AARs, scenarios                       |
| API             | `backend/main.py`             | FastAPI REST                                        |
| UI              | `frontend/app.py`             | Streamlit tabbed interface                          |

---

## Datasets & APIs

| Source                        | Usage                                           | Auth         |
| ----------------------------- | ----------------------------------------------- | ------------ |
| **GDELT Doc 2.0**             | Live news → tension signals, actor extraction   | None         |
| **ACLED**                     | Conflict events schema (seed fallback included) | Optional key |
| **UCDP GED v24.1**            | Armed conflict history, intensity scoring       | None         |
| **Overpass / OSM**            | Critical infrastructure by geographic bbox      | None         |
| **JP 3-12 / JP 5-0 / JP 3-0** | Joint doctrine corpus in Chroma vector store    | None (local) |
| **CSIS Analysis Library**     | Strategic framing for AAR citations             | None (local) |
| **MITRE ATT&CK for ICS**      | Technique corpus (T0801–T0867)                  | None (local) |
| **CISA Advisories**           | Volt Typhoon / APT profiles                     | None (local) |

All sources have local seed fallbacks — the engine never blocks on unavailable APIs.

### Region → bbox mapping (OSM)

`overpass_adapter.bbox_for_region()` resolves free-text scenario queries to geographic bounding boxes for live infrastructure queries:

```
"Volt Typhoon Texas power grid"  →  25.8,-107.0,36.5,-93.5  (Texas)
"Taiwan Strait scenario"         →  20.0,117.0,28.0,124.0   (Taiwan Strait)
"Ukraine power grid crisis"      →  44.0,22.1,52.4,40.2     (Ukraine)
"Iran IRGC cyber"                →  25.0,44.0,40.0,63.5     (Iran)
```

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

### Using the UI

1. In the sidebar, type a scenario query under **"New Scenario"** — e.g. `Volt Typhoon Texas power grid`
2. Click **⚡ Launch Scenario** — the engine fuses GDELT + ACLED + UCDP + OSM + doctrine (~10-15s)
3. The **Brief** tab shows: Tension Score, Conflict Score, Infrastructure at Risk, Doctrine Notes, Strategic Assessment
4. Switch to **Move** and describe a Blue Team defensive action in plain English
5. Hit **Execute Move** — get adjudication, Red Cell response, and AAR with JP 3-12 citations

### Smoke test (curl)

```bash
# Seed a live scenario
curl -s -X POST http://localhost:8029/scenarios/seed \
  -H 'content-type: application/json' \
  -d '{"query":"Volt Typhoon Texas power grid","use_api":true,"use_acled":true}' \
  | python3 -m json.tool

# Submit a Blue move
curl -s -X POST http://localhost:8029/turn \
  -H 'content-type: application/json' \
  -d '{"blue_move":"Isolate the SCADA HMI and hunt for persistence on the jump host"}' \
  | python3 -m json.tool

# Active scenario
curl http://localhost:8029/scenario | python3 -m json.tool

# Reset demo
curl -X POST http://localhost:8029/reset
```

---

## Fused Scenario Schema

Every seeded scenario carries a full intelligence picture:

```json
{
  "tension_score": 72,
  "conflict_score": 64,
  "infrastructure_risk_score": 80,
  "adversary_aggression_score": 85,
  "scenario_summary": "Intelligence fusion across 21 open-source events...",
  "doctrine_notes": ["JP 3-12: Persistent engagement preferred...", "..."],
  "strategic_notes": ["CSIS: PRC pre-positioning signals...", "..."],
  "infrastructure": [{"type": "power_substation", "criticality": "high", ...}],
  "recommended_red_posture": "aggressive",
  "sources_used": ["gdelt", "acled", "ucdp"]
}
```

---

## Canned Scenarios

Pre-loaded for instant demo use (no API wait):

| ID                    | Name                    | Threat                                            |
| --------------------- | ----------------------- | ------------------------------------------------- |
| `tidewatch-001`       | Operation Tidewatch     | Nation-state APT in power utility SCADA (default) |
| `port-cyber-001`      | Operation Tidegate      | IRGC-class actor in container port terminal       |
| `grid-substation-001` | Operation Ironwood      | Volt Typhoon LOTL in substation OT                |
| `telecom-bgp-001`     | Operation Phantom Route | DPRK BGP hijack at Tier-1 ISP                     |

Switch via the sidebar dropdown or `POST /scenarios/select`.

---

## Full directory tree

```
ghostmesh/
├── backend/
│   ├── main.py          FastAPI routes (turns, scenarios, history, reset)
│   ├── db.py            SQLite persistence (turns, aars, scenarios tables)
│   ├── parser.py        NL → structured move intent
│   ├── adjudicator.py   Probabilistic outcome + doctrine note
│   ├── redcell.py       State-machine adversary engine
│   ├── aar.py           AAR + JP 3-12 / CSIS retrieval citations
│   └── schemas.py       Pydantic models (shared contracts)
├── retrieval/
│   ├── ingest.py        Corpus → Chroma (CLI, idempotent)
│   ├── service.py       retrieve() — Chroma primary, TF-IDF fallback
│   ├── fallback.py      Pure-python TF-IDF (no deps)
│   └── corpus/          Markdown files: MITRE, APT, defense, JCS doctrine, CSIS
├── scenarios/
│   ├── seeder.py        OSINT fusion pipeline (GDELT + ACLED + UCDP + OSM)
│   ├── mapping.py       Events → FusedScenario (scores, doctrine, summary)
│   └── canned/          Pre-built scenario JSONs
├── sources/
│   ├── gdelt_adapter.py   GDELT Doc 2.0 client
│   ├── acled_adapter.py   ACLED conflict events (seed fallback)
│   ├── ucdp_adapter.py    UCDP GED armed conflict history
│   └── overpass_adapter.py  OSM infrastructure + bbox_for_region()
├── data/
│   └── seed/
│       ├── osm_sample.json      Critical infrastructure fallback
│       ├── ucdp_sample.json     Armed conflict history fallback
│       ├── acled_sample.json    Conflict events fallback
│       └── doctrine/            JP 3-12 excerpts for retrieval
├── frontend/
│   └── app.py           Streamlit (tabs: Brief / Move / Result / AAR / Timeline)
├── docs/
│   ├── DEMO_SCRIPT.md
│   ├── JUDGE_TALKING_POINTS.md
│   └── ARCHITECTURE.md
└── requirements.txt
```

---

## Troubleshooting

**Chroma cold-start** — run `python -m retrieval.ingest` once before the demo. Warmup is called on API startup but ingest must run first.

**GDELT timeout** — offline fallback activates automatically within 4s, returns seed data.

**UCDP API unavailable** — falls back to `data/seed/ucdp_sample.json` (5 real armed conflicts).

**OSM / Overpass timeout** — falls back to `data/seed/osm_sample.json` (US critical infrastructure).

**Port collision** — change `--port 8029` and update `api_url` in `frontend/app.py` line 996.

**`chromadb` not installed** — TF-IDF fallback activates automatically. Retrieval still works.

**`ModuleNotFoundError: retrieval`** — run all commands from the `ghostmesh/` directory.
