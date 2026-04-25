from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend import db, scenario as scenario_mod
from backend.adjudicator import adjudicate
from backend.parser import parse_move
from backend.redcell import generate_red_response
from backend.schemas import (
    Adjudication,
    ParsedMove,
    RedMove,
    Scenario,
    TurnRequest,
    TurnResponse,
)

app = FastAPI(
    title="GhostMesh",
    description="AI-powered cyber wargaming engine — vertical slice",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    db.init_db()


@app.get("/scenario", response_model=Scenario, summary="Active scenario")
def get_scenario() -> Dict[str, Any]:
    return scenario_mod.get_scenario()


@app.post("/turn", response_model=TurnResponse, summary="Submit a Blue move")
def submit_turn(req: TurnRequest) -> Dict[str, Any]:
    if not req.blue_move.strip():
        raise HTTPException(status_code=400, detail="blue_move must not be empty")

    sc = scenario_mod.get_scenario()

    parsed_dict = parse_move(req.blue_move)
    # Use a temporary turn_id for seeding — real id assigned after insert
    temp_id = hash(req.blue_move + datetime.now(timezone.utc).isoformat()) % 100_000
    adjudication_dict = adjudicate(parsed_dict, sc, temp_id)
    red_dict = generate_red_response(parsed_dict, adjudication_dict, sc, temp_id)

    ts = datetime.now(timezone.utc).isoformat()
    turn_id = db.save_turn(
        ts=ts,
        scenario_id=sc["id"],
        blue_move=req.blue_move,
        parsed=parsed_dict,
        adjudication=adjudication_dict,
        red=red_dict,
    )

    return {
        "turn_id": turn_id,
        "ts": ts,
        "blue_move": req.blue_move,
        "parsed": parsed_dict,
        "adjudication": adjudication_dict,
        "red": red_dict,
    }


@app.get("/history", summary="Turn history")
def get_history() -> List[Dict[str, Any]]:
    return db.list_turns()


@app.post("/reset", summary="Wipe turn history (demo reset)")
def reset() -> Dict[str, str]:
    db.reset_turns()
    return {"status": "ok", "message": "Turn history cleared"}
