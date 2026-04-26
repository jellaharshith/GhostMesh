from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend import db, scenario as scenario_mod
from scenarios import seeder as scenario_seeder
from backend.schemas import SeedRequest, SelectRequest, CreateScenarioRequest, ParseTextRequest
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
    try:
        from retrieval.service import warmup
        warmup()
    except Exception:
        pass


@app.get("/scenario", response_model=Scenario, summary="Active scenario")
def get_scenario() -> Dict[str, Any]:
    return scenario_mod.get_scenario()


@app.get("/scenarios", summary="List all scenarios")
def list_scenarios():
    canned = [s for s in scenario_seeder.list_canned()]
    db_scenarios = db.list_scenarios()
    # Merge: canned first, then DB-saved (exclude canned IDs already included)
    canned_ids = {s["id"] for s in canned}
    extra = [row["scenario"] for row in db_scenarios if row["id"] not in canned_ids]
    return canned + extra


@app.post("/scenarios/seed", response_model=Scenario, summary="Seed a scenario from GDELT/ACLED or use canned")
def seed_scenario(body: SeedRequest):
    if body.use_api:
        sc = scenario_seeder.seed_from_api(
            body.query,
            timeout_s=4.0,
            use_acled=body.use_acled,
            country=body.country,
        )
    else:
        sc = scenario_seeder.get_scenario()
    return sc


@app.post("/scenarios/select", response_model=Scenario, summary="Set active scenario")
def select_scenario(body: SelectRequest):
    sc = scenario_seeder.select(body.scenario_id)
    if sc is None:
        raise HTTPException(status_code=404, detail=f"Scenario '{body.scenario_id}' not found")
    return sc


@app.post("/scenarios/create", response_model=Scenario, summary="Create and set custom scenario")
def create_scenario(body: CreateScenarioRequest):
    import json
    from pathlib import Path

    scenario_dict = body.dict()
    scenario_dict["sources_used"] = ["custom"]

    canned_dir = Path(__file__).parent.parent / "scenarios" / "canned"
    canned_dir.mkdir(parents=True, exist_ok=True)
    scenario_file = canned_dir / f"{body.id}.json"

    with open(scenario_file, "w") as f:
        json.dump(scenario_dict, f, indent=2)

    scenario_seeder.select(body.id)
    return scenario_dict


@app.post("/scenarios/parse", response_model=Scenario, summary="Parse plain-English scenario text and run it")
def parse_and_run_scenario(body: ParseTextRequest):
    import json, re, hashlib
    from pathlib import Path

    text = body.text.strip()

    # Generate stable ID from content
    sc_hash = hashlib.md5(text.encode()).hexdigest()[:8]
    sc_id = f"custom-{sc_hash}"

    # Extract name: first non-empty line, or first heading
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    name_line = lines[0].lstrip("#").strip() if lines else "Custom Scenario"
    name = re.sub(r"[*_`]", "", name_line)[:80]

    text_lower = text.lower()

    # Detect tension level
    tension = 5.0
    if any(w in text_lower for w in ["high", "7", "8", "9", "10", "critical", "severe", "war"]):
        tension = 7.5
    if any(w in text_lower for w in ["low", "1", "2", "3", "minimal"]):
        tension = 2.5

    # Detect actor type → red posture
    actor_hints = {
        "volt typhoon": "PRC Volt Typhoon-class LOTL actor. Uses native Windows tools, compromised contractor credentials. Stealth priority: stay below detection threshold. Escalation: hold and expand footprint.",
        "sandworm": "GRU Sandworm-class actor. Destructive capability. Targets OT/ICS. Willing to cause visible disruption. Escalation: escalate if Blue gains ground.",
        "lazarus": "DPRK Lazarus-class actor. Financial and espionage motives. Uses custom malware. Escalation: hold unless eviction imminent.",
        "irgc": "IRGC-affiliated actor. Hacktivist-style messaging. Targets visible infrastructure. Escalation: escalate for propaganda value.",
        "hybrid": "State-backed hybrid warfare actor. Combines cyber with disinformation and kinetic pressure. Ambiguous attribution intentional. Escalation: measured, test thresholds.",
        "ransomware": "Criminal ransomware actor. Financially motivated. Deploy encrypt-on-trigger payloads. Escalation: escalate if ransom not met.",
    }
    red_posture = "State-sponsored actor using LOTL techniques. Maintains persistence via compromised credentials. Stealth priority. Escalation: hold and monitor Blue response."
    for key, posture in actor_hints.items():
        if key in text_lower:
            red_posture = posture
            break

    # Detect assets from infrastructure keywords
    asset_map = {
        "scada": ("SCADA-CONTROL", "SCADA Control System", "at-risk"),
        "hmi": ("HMI-PRIMARY", "HMI Workstation", "at-risk"),
        "vpn": ("VPN-GATEWAY", "VPN Access Gateway", "compromised"),
        "contractor": ("CONTRACTOR-VPN", "Contractor VPN", "compromised"),
        "substation": ("SUBSTATION-RTU", "Substation RTU", "at-risk"),
        "load balanc": ("LB-SERVER", "Load Balancing Server", "at-risk"),
        "historian": ("SCADA-HISTORIAN", "SCADA Historian", "at-risk"),
        "firewall": ("OT-FIREWALL", "OT Boundary Firewall", "online"),
        "plc": ("PLC-CONTROL", "Programmable Logic Controller", "at-risk"),
        "rtu": ("RTU-FIELD", "Remote Terminal Unit", "at-risk"),
        "bgp": ("BGP-ROUTER", "BGP Route Reflector", "compromised"),
        "dns": ("DNS-SERVER", "DNS Infrastructure", "at-risk"),
        "power grid": ("GRID-CONTROL", "Power Grid Control", "at-risk"),
        "energy": ("ENERGY-MGMT", "Energy Management System", "at-risk"),
        "water": ("WATER-SCADA", "Water Treatment SCADA", "at-risk"),
        "port": ("PORT-TOS", "Terminal Operating System", "at-risk"),
        "crane": ("CRANE-PLC", "Crane Control PLC", "at-risk"),
    }
    assets = []
    seen = set()
    for keyword, (aname, atype, astatus) in asset_map.items():
        if keyword in text_lower and aname not in seen:
            assets.append({"name": aname, "type": atype, "status": astatus})
            seen.add(aname)

    if not assets:
        assets = [
            {"name": "PRIMARY-SYSTEM", "type": "Critical Infrastructure System", "status": "at-risk"},
            {"name": "ACCESS-GATEWAY", "type": "Access Gateway", "status": "compromised"},
            {"name": "MONITOR-CONSOLE", "type": "Monitoring Console", "status": "online"},
        ]

    # Auto-generate blue objectives from keywords
    objectives = []
    if any(w in text_lower for w in ["vpn", "contractor", "credential"]):
        objectives.append("Identify and revoke compromised contractor credentials")
    if any(w in text_lower for w in ["persistence", "scheduled task", "backdoor"]):
        objectives.append("Hunt and remove adversary persistence mechanisms")
    if any(w in text_lower for w in ["scada", "ics", "ot", "plc", "rtu", "hmi"]):
        objectives.append("Protect OT/ICS systems from adversary lateral movement")
    if any(w in text_lower for w in ["outage", "disruption", "blackout", "load"]):
        objectives.append("Prevent operational disruption and restore normal operations")
    if any(w in text_lower for w in ["attribution", "attrib", "actor", "nation"]):
        objectives.append("Attribute adversary activity and coordinate with authorities")
    if not objectives:
        objectives = [
            "Detect and contain adversary activity",
            "Preserve operational continuity",
            "Coordinate incident response",
        ]

    scenario_dict = {
        "id": sc_id,
        "name": name,
        "brief": text,
        "blue_objectives": objectives,
        "red_posture": red_posture,
        "assets": assets,
        "tension_level": tension,
        "actor_relationships": [],
        "recent_events": [],
        "sources_used": ["custom"],
    }

    canned_dir = Path(__file__).parent.parent / "scenarios" / "canned"
    canned_dir.mkdir(parents=True, exist_ok=True)
    with open(canned_dir / f"{sc_id}.json", "w") as f:
        json.dump(scenario_dict, f, indent=2)

    scenario_seeder.select(sc_id)
    return scenario_dict


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
