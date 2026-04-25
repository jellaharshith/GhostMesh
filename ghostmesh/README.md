# GhostMesh — Vertical Slice

AI-powered cyber wargaming engine. One scenario, full turn loop: parse → adjudicate → red cell → persist → UI.

## Quick start

```bash
# from ghostmesh/ directory
# requires Python 3.12 (pydantic-core wheel not yet on 3.14)
/usr/local/bin/python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# terminal 1 — API (port 8029)
uvicorn backend.main:app --reload --port 8029

# terminal 2 — UI (port 8501)
streamlit run frontend/app.py
```

- UI: http://localhost:8501  
- API docs: http://localhost:8029/docs

## Smoke test

```bash
# scenario
curl http://localhost:8029/scenario | python -m json.tool

# submit a turn
curl -X POST http://localhost:8029/turn \
  -H 'content-type: application/json' \
  -d '{"blue_move":"Isolate the SCADA HMI from the corporate VLAN and hunt for persistence on the jump host"}'

# history
curl http://localhost:8029/history | python -m json.tool

# reset
curl -X POST http://localhost:8029/reset
```

## Architecture

```
ghostmesh/
├── backend/
│   ├── main.py          FastAPI routes
│   ├── db.py            SQLite persistence
│   ├── scenario.py      Canned scenario
│   ├── parser.py        NL → structured intent
│   ├── adjudicator.py   Probabilistic outcome
│   ├── redcell.py       Adversary response
│   └── schemas.py       Pydantic models
├── frontend/
│   └── app.py           Streamlit UI
├── data/
│   └── ghostmesh.db     Created at runtime
└── requirements.txt
```
