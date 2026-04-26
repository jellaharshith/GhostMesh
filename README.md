# GhostMesh

GhostMesh is an AI-assisted cyber wargaming platform that runs locally.  
Describe an operational scenario in plain English, fuse live and seeded intelligence into a mission brief, execute Blue Team actions, and receive probabilistic adjudication, adaptive Red Cell responses, and doctrine-grounded after-action reviews.

Built for the SCSP Hackathon and designed for operators, analysts, and exercise planners who need fast, explainable cyber decision support.

---

## Architecture

```
Scenario query (plain English)
         │
         ▼
┌──────────────────────────────────────────────────────────────────┐
│                      Intelligence Fusion                          │
│  GDELT (news/tension) · LiveUAMap (live conflict markers)         │
│  UCDP (wars) · GTD (historical baseline)                          │
│  Overpass/OSM (infrastructure) · OpenTopography (SRTM terrain)    │
│  Chroma (JCS JP 1-0/3-0/3-12/3-13/3-28/5-0 + CSIS + MITRE)        │
└──────────────────────────────┬───────────────────────────────────┘
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

| Module          | File                                | Purpose                                                       |
| --------------- | ----------------------------------- | ------------------------------------------------------------- |
| Parser          | `backend/parser.py`                 | NL → structured intent (keyword, no LLM)                      |
| Adjudicator     | `backend/adjudicator.py`            | Probabilistic outcome + doctrine note                         |
| Red Cell        | `backend/redcell.py`                | Adaptive adversary state machine (LLM polish optional)        |
| AAR             | `backend/aar.py`                    | Deterministic debrief + JCS / CSIS / MITRE citations          |
| Retrieval       | `retrieval/service.py`              | Chroma semantic / TF-IDF fallback                             |
| Scenario Seeder | `scenarios/seeder.py`               | OSINT fusion: GDELT + LiveUAMap + UCDP + GTD + OSM + terrain  |
| Mapping         | `scenarios/mapping.py`              | Events → FusedScenario with scores + doctrine notes           |
| GDELT           | `sources/gdelt_adapter.py`          | Live news tension signals                                     |
| LiveUAMap       | `sources/liveuamap_adapter.py`      | Live conflict markers (24h disk cache + seed)                 |
| UCDP            | `sources/ucdp_adapter.py`           | Armed conflict history (UCDP GED API / seed)                  |
| GTD             | `sources/gtd_adapter.py`            | Global Terrorism DB historical baseline (~2K-row sample + HF) |
| Overpass        | `sources/overpass_adapter.py`       | OSM infrastructure (bbox from region text)                    |
| OpenTopography  | `sources/opentopography_adapter.py` | SRTM elevation summary (live with key, seed fallback)         |
| DB              | `backend/db.py`                     | SQLite turns, AARs, scenarios                                 |
| API             | `backend/main.py`                   | FastAPI REST (+ /events/live, /history/gtd, /terrain)         |
| UI              | `frontend/app.py`                   | Streamlit tabbed interface (+ Live Intel panel)               |

---

## Datasets & APIs

| Source                                        | Usage                                                  | Auth                  |
| --------------------------------------------- | ------------------------------------------------------ | --------------------- |
| **GDELT Doc 2.0**                             | Live news → tension signals, actor extraction          | None                  |
| **LiveUAMap**                                 | Live conflict markers, 24h disk cache + seed           | None                  |
| **UCDP GED v24.1**                            | Armed conflict history, intensity scoring              | None                  |
| **Global Terrorism Database**                 | Historical baseline, ~2K-row stratified sample bundled | None (HF mirror opt-in) |
| **Overpass / OSM**                            | Critical infrastructure by geographic bbox             | None                  |
| **OpenTopography (SRTM DEMs)**                | Terrain summary (min/mean/max elevation, class)        | Optional key          |
| **JCS JP 1-0 / 3-0 / 3-12 / 3-13 / 3-28 / 5-0** | Joint doctrine corpus in Chroma vector store           | None (local)          |
| **CSIS Analysis Library**                     | Strategic framing for AAR citations                    | None (local)          |
| **MITRE ATT&CK for ICS**                      | Technique corpus (T0801–T0867)                         | None (local)          |
| **CISA Advisories**                           | Volt Typhoon / APT profiles                            | None (local)          |

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

### Configuration (optional)

Copy the example environment file and only set what you need:

```bash
cd ghostmesh
cp .env.example .env
# Edit .env — never commit the real file (it is gitignored)
```

| Variable            | Required | Purpose |
| ------------------- | -------- | ------- |
| `ANTHROPIC_API_KEY` | No       | Enables LLM-assisted move parsing, Red Cell polish, and richer AAR when the key is set. Without it, deterministic paths still run. |
| `OPENTOPO_API_KEY`  | No       | Live SRTM terrain from OpenTopography. Without it, seeded `data/seed/elevation_seed.json` is used for known regions. |
| `GTD_USE_HF=1`      | No       | One-shot pull from a public HuggingFace GTD mirror; default is the bundled `data/seed/gtd_sample.csv`. |

The `anthropic` package is listed in `requirements.txt` for optional LLM features.

### Using the UI

1. In the sidebar, enter a scenario query under **New Scenario**  
   Example: `Volt Typhoon Texas power grid`
2. Enter a **First Blue Move** in plain English (required before launch)
3. Click **⚡ Launch Scenario**  
   GhostMesh seeds the scenario, fuses intelligence sources, and immediately executes your first move.
4. Review the **Brief** tab:
   - Mission brief and fused intelligence picture
   - Scenario objectives, red posture, and infrastructure context
   - **Mission Brief Results** (move parse, adjudication, red response, and AAR) from the launch move
5. Use the **Move** tab for additional turns, then review **Result**, **AAR**, and **Timeline** as needed.

### Operator Workflow (at a glance)

- **Brief:** Understand the scenario and evaluate immediate operational context.
- **Move:** Submit follow-on Blue Team actions.
- **Result:** Inspect outcome metrics and rationale for the latest turn.
- **AAR:** Read doctrine-grounded narrative debrief with citations.
- **Timeline:** Review the full multi-turn campaign progression.

### Smoke test (curl)

```bash
# Seed a live scenario (GDELT + LiveUAMap + UCDP + GTD + OSM + OpenTopography)
curl -s -X POST http://localhost:8029/scenarios/seed \
  -H 'content-type: application/json' \
  -d '{"query":"Volt Typhoon Texas power grid","use_api":true}' \
  | python3 -m json.tool

# Live merged event feed for a region
curl 'http://localhost:8029/events/live?region=Ukraine&hours=24&limit=20' \
  | python3 -m json.tool

# Historical baseline from GTD
curl 'http://localhost:8029/history/gtd?region=Iran&start_year=2010&end_year=2020&limit=20' \
  | python3 -m json.tool

# Terrain summary (min/mean/max elevation, terrain class)
curl 'http://localhost:8029/terrain?region=Taiwan%20Strait' | python3 -m json.tool

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
  "historical_baseline": [{"year": 2014, "location": "Donetsk", "summary": "..."}],
  "terrain": {"min_elev_m": 80, "mean_elev_m": 210, "max_elev_m": 540, "terrain_class": "lowland"},
  "recommended_red_posture": "aggressive",
  "sources_used": ["gdelt", "liveuamap", "ucdp", "gtd"]
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
│   ├── schemas.py       Pydantic models (shared contracts)
│   └── tests/           Pytest (parser / schema cases; LLM paths monkey-patched)
├── retrieval/
│   ├── ingest.py        Corpus → Chroma (CLI, idempotent)
│   ├── service.py       retrieve() — Chroma primary, TF-IDF fallback
│   ├── fallback.py      Pure-python TF-IDF (no deps)
│   └── corpus/          Markdown files: MITRE, APT, defense, JCS doctrine, CSIS
├── scenarios/
│   ├── seeder.py        OSINT fusion (GDELT + LiveUAMap + UCDP + GTD + OSM + OpenTopography)
│   ├── mapping.py       Events → FusedScenario (scores, doctrine, summary)
│   └── canned/          Pre-built scenario JSONs
├── sources/
│   ├── gdelt_adapter.py           GDELT Doc 2.0 client
│   ├── liveuamap_adapter.py       LiveUAMap conflict markers (24h cache + seed)
│   ├── ucdp_adapter.py            UCDP GED armed conflict history
│   ├── gtd_adapter.py             Global Terrorism DB (bundled CSV + optional HF)
│   ├── overpass_adapter.py        OSM infrastructure + bbox_for_region()
│   └── opentopography_adapter.py  SRTM elevation summary (live + seed)
├── data/
│   └── seed/
│       ├── osm_sample.json        Critical infrastructure fallback
│       ├── ucdp_sample.json       Armed conflict history fallback
│       ├── liveuamap_sample.json  Live conflict markers fallback
│       ├── gtd_sample.csv         ~2K-row stratified GTD sample
│       ├── elevation_seed.json    Per-region SRTM elevation summaries
│       └── doctrine/              JCS / CSIS / MITRE excerpts for retrieval
├── frontend/
│   └── app.py           Streamlit (tabs: Brief / Move / Result / AAR / Timeline)
├── docs/
│   ├── DEMO_SCRIPT.md
│   ├── JUDGE_TALKING_POINTS.md
│   └── ARCHITECTURE.md
└── requirements.txt
```

---

## Development

From `ghostmesh/` with the virtualenv active:

```bash
pip install pytest
python -m pytest backend/tests/ -q
```

---

## Troubleshooting

**Chroma cold-start** — run `python -m retrieval.ingest` once before the demo. Warmup is called on API startup but ingest must run first.

**GDELT timeout** — offline fallback activates automatically within 4s, returns seed data.

**UCDP API unavailable** — falls back to `data/seed/ucdp_sample.json` (5 real armed conflicts).

**LiveUAMap API unavailable** — falls back to `data/seed/liveuamap_sample.json` (~30 normalized recent markers).

**OSM / Overpass timeout** — falls back to `data/seed/osm_sample.json` (US critical infrastructure).

**OpenTopography key unset** — `/terrain` and the seeded `terrain` block read from `data/seed/elevation_seed.json` (precomputed for ~12 theaters). Set `OPENTOPO_API_KEY` for live SRTM queries.

**GTD HuggingFace mirror disabled** — by default the bundled `data/seed/gtd_sample.csv` (~2K rows, stratified by region/year) is used. Set `GTD_USE_HF=1` to opt in to a one-shot mirror pull.

**Port collision** — change `--port 8029` and update `API_URL` in `frontend/app.py` (search for `API_URL = `, default `http://localhost:8029`).

**`chromadb` not installed** — TF-IDF fallback activates automatically. Retrieval still works.

**`ModuleNotFoundError: retrieval`** — run all commands from the `ghostmesh/` directory.
