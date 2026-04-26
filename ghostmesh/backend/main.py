from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend import db, scenario as scenario_mod
from backend.aar import generate_aar
from backend.adjudicator import adjudicate
from backend.parser import parse_move
from backend.redcell import generate_red_response
from backend.schemas import (
    AARResponse,
    AfterAction,
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

    prior_history = db.list_turns()[:-1]  # exclude the just-saved turn
    aar_dict = generate_aar(
        turn_id=turn_id,
        scenario=sc,
        parsed=parsed_dict,
        adjudication=adjudication_dict,
        red=red_dict,
        history=prior_history,
    )
    db.save_aar(
        turn_id=turn_id,
        scenario_id=sc["id"],
        generated_ts=aar_dict["generated_ts"],
        aar=aar_dict,
        ui_text=aar_dict["ui_text"],
    )

    return {
        "turn_id": turn_id,
        "ts": ts,
        "blue_move": req.blue_move,
        "parsed": parsed_dict,
        "adjudication": adjudication_dict,
        "red": red_dict,
        "aar": aar_dict,
    }


@app.get("/history", summary="Turn history")
def get_history() -> List[Dict[str, Any]]:
    return db.list_turns()


@app.get("/aar/{turn_id}", response_model=AARResponse, summary="Fetch AAR for a turn")
def get_aar_endpoint(turn_id: int) -> Dict[str, Any]:
    aar = db.get_aar(turn_id)
    if not aar:
        raise HTTPException(status_code=404, detail=f"No AAR for turn {turn_id}")
    return {"aar": aar}


@app.post("/aar/{turn_id}/regenerate", response_model=AARResponse, summary="Regenerate AAR for a turn")
def regenerate_aar(turn_id: int) -> Dict[str, Any]:
    turns = db.list_turns()
    turn = next((t for t in turns if t["turn_id"] == turn_id), None)
    if not turn:
        raise HTTPException(status_code=404, detail=f"Turn {turn_id} not found")
    sc = scenario_mod.get_scenario()
    prior = [t for t in turns if t["turn_id"] < turn_id]
    aar = generate_aar(turn_id, sc, turn["parsed"], turn["adjudication"], turn["red"], prior)
    db.save_aar(turn_id, sc["id"], aar["generated_ts"], aar, aar["ui_text"])
    return {"aar": aar}


@app.post("/reset", summary="Wipe turn history (demo reset)")
def reset() -> Dict[str, str]:
    db.reset_turns()
    return {"status": "ok", "message": "Turn history cleared"}
