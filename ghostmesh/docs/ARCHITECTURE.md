# GhostMesh — Architecture

## Turn flow

```
User (plain English)
        │
        ▼
  [Parser]  backend/parser.py
  • Keyword extraction → action, target, technique_family
  • Stealth/risk classification
  • Confidence scoring (0.1–1.0)
  • No LLM
        │
        ▼ ParsedMove dict
  [Adjudicator]  backend/adjudicator.py
  • Seeded RNG (turn_id × 31337 + hash(action))
  • Composited score: effectiveness × execution × preparation × target-fit
  • 4-class outcome sampling: full/strong_partial/weak_partial/failure
  • Conditional attribution: P(attrib) = P(attrib|detect) × P(detect)
  • Retrieval hook: appends MITRE/defense doctrine note to rationale
        │
        ▼ Adjudication dict
  [Red Cell]  backend/redcell.py
  • Replays full turn history → pressure, footholds, urgency
  • Posture: aggressive | opportunistic | conservative | desperate
  • Tier: retreat | hold | escalate → escalate_destructive
  • 48-variant playbook (12 actions × 4 tiers)
  • APT doctrine table: 14 doctrine-biased overrides
  • Retrieval hook: appends APT TTP citation to rationale
        │
        ▼ RedMove dict
  [DB]  backend/db.py
  • INSERT INTO turns → get real turn_id
        │
        ▼ turn_id
  [AAR]  backend/aar.py
  • Effect tag parsing → outcome_class
  • Deterministic what/why/risks/cascades/recommendation
  • Retrieval hook: doctrine citations appended to why_it_happened
  • _render_ui_text: markdown + severity icons + horizon icons + sources
  • citations: List[RetrievalSnippet]
        │
        ▼ AfterAction dict (with citations)
  [DB]  backend/db.py
  • INSERT OR REPLACE INTO aars
        │
        ▼ TurnResponse
  [Streamlit UI]  frontend/app.py
  • Tabs: Brief | Move | Result | AAR | Timeline
  • Progress bars, cascading effects, AAR citations
```

## Retrieval layer

```
retrieval/corpus/*.md (19 files)
         │
         ▼ python -m retrieval.ingest
  [Chroma PersistentClient]  data/chroma/
  • Collection: ghostmesh-doctrine
  • Embedding: DefaultEmbeddingFunction (MiniLM-L6-v2 via onnxruntime)
  • ~57 chunks
         │
         ▼ retrieve(query, k, tags)
  [service.py]
  • Lazy-load chroma client + collection
  • 250ms timeout via ThreadPoolExecutor
  • On failure → fallback.tfidf_search()
         │
         ▼ List[RetrievalSnippet]
  [Adjudicator / Red Cell / AAR]
```

## Scenario seeder

```
scenarios/canned/*.json (4 files)
         │
         ▼ list_canned()
  [seeder.py]
  • In-memory _active cache + SQLite is_active flag
  • Resolution: scenario_id → cache → DB → tidewatch default

  seed_from_api(query) →
    gdelt.fetch_articles(query, timeout=4s)
         │ on failure → canned fallback
         ▼
    mapping.articles_to_scenario(articles, query)
    • Infra keyword table → asset preset
    • Actor keyword table → red posture
    • Deterministic id = sha1(query + blob)[:8]
         │
         ▼ Scenario dict
    db.save_scenario() → persisted
```

## Data model

```
SQLite: data/ghostmesh.db

turns
  id INTEGER PK AUTOINCREMENT
  ts TEXT
  scenario_id TEXT
  blue_move TEXT
  parsed_json TEXT (JSON)
  adjudication_json TEXT (JSON)
  red_json TEXT (JSON)

aars
  id INTEGER PK AUTOINCREMENT
  turn_id INTEGER UNIQUE
  scenario_id TEXT
  generated_ts TEXT
  aar_json TEXT (JSON — includes citations[])
  ui_text TEXT (markdown)

scenarios
  id TEXT PK
  name TEXT
  json TEXT (JSON)
  created_ts TEXT
  is_active INTEGER (0/1)
```

## API surface

```
GET  /scenario              → active Scenario
GET  /scenarios             → List[Scenario] (canned + DB-saved)
POST /scenarios/seed        → Scenario (GDELT or canned fallback)
POST /scenarios/select      → Scenario (set active)
POST /turn                  → TurnResponse (full pipeline)
GET  /history               → List[turn dicts]
GET  /aar/{turn_id}         → AARResponse
POST /aar/{turn_id}/regenerate → AARResponse
POST /reset                 → clears turns + aars
```
