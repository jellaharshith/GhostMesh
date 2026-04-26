import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = Path(__file__).parent.parent / "data" / "ghostmesh.db"


def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS turns (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                ts               TEXT    NOT NULL,
                scenario_id      TEXT    NOT NULL,
                blue_move        TEXT    NOT NULL,
                parsed_json      TEXT    NOT NULL,
                adjudication_json TEXT   NOT NULL,
                red_json         TEXT    NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS aars (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                turn_id      INTEGER NOT NULL UNIQUE,
                scenario_id  TEXT    NOT NULL,
                generated_ts TEXT    NOT NULL,
                aar_json     TEXT    NOT NULL,
                ui_text      TEXT    NOT NULL
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_aars_turn ON aars(turn_id)"
        )
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scenarios (
                id          TEXT PRIMARY KEY,
                name        TEXT NOT NULL,
                json        TEXT NOT NULL,
                created_ts  TEXT NOT NULL,
                is_active   INTEGER NOT NULL DEFAULT 0
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_scenarios_active ON scenarios(is_active)"
        )
        conn.commit()


def save_turn(
    ts: str,
    scenario_id: str,
    blue_move: str,
    parsed: Dict[str, Any],
    adjudication: Dict[str, Any],
    red: Dict[str, Any],
) -> int:
    with _conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO turns (ts, scenario_id, blue_move, parsed_json, adjudication_json, red_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                ts,
                scenario_id,
                blue_move,
                json.dumps(parsed),
                json.dumps(adjudication),
                json.dumps(red),
            ),
        )
        conn.commit()
        return cur.lastrowid


def list_turns() -> List[Dict[str, Any]]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT id, ts, scenario_id, blue_move, parsed_json, adjudication_json, red_json FROM turns ORDER BY id"
        ).fetchall()
    result = []
    for row in rows:
        result.append({
            "turn_id": row["id"],
            "ts": row["ts"],
            "scenario_id": row["scenario_id"],
            "blue_move": row["blue_move"],
            "parsed": json.loads(row["parsed_json"]),
            "adjudication": json.loads(row["adjudication_json"]),
            "red": json.loads(row["red_json"]),
        })
    return result


def save_aar(
    turn_id: int,
    scenario_id: str,
    generated_ts: str,
    aar: Dict[str, Any],
    ui_text: str,
) -> int:
    with _conn() as conn:
        cur = conn.execute(
            """
            INSERT OR REPLACE INTO aars (turn_id, scenario_id, generated_ts, aar_json, ui_text)
            VALUES (?, ?, ?, ?, ?)
            """,
            (turn_id, scenario_id, generated_ts, json.dumps(aar), ui_text),
        )
        conn.commit()
        return cur.lastrowid


def get_aar(turn_id: int) -> Optional[Dict[str, Any]]:
    with _conn() as conn:
        row = conn.execute(
            "SELECT aar_json FROM aars WHERE turn_id = ?", (turn_id,)
        ).fetchone()
    return json.loads(row["aar_json"]) if row else None


def list_aars() -> List[Dict[str, Any]]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT aar_json FROM aars ORDER BY turn_id"
        ).fetchall()
    return [json.loads(r["aar_json"]) for r in rows]


def reset_turns() -> None:
    with _conn() as conn:
        conn.execute("DELETE FROM aars")
        conn.execute("DELETE FROM turns")
        conn.commit()


def save_scenario(scenario_id: str, name: str, scenario_json: Dict[str, Any], created_ts: str) -> None:
    with _conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO scenarios (id, name, json, created_ts, is_active) VALUES (?, ?, ?, ?, 0)",
            (scenario_id, name, json.dumps(scenario_json), created_ts),
        )
        conn.commit()


def get_active_scenario() -> Optional[Dict[str, Any]]:
    with _conn() as conn:
        row = conn.execute(
            "SELECT json FROM scenarios WHERE is_active = 1 LIMIT 1"
        ).fetchone()
    return json.loads(row["json"]) if row else None


def set_active_scenario(scenario_id: str) -> None:
    with _conn() as conn:
        conn.execute("UPDATE scenarios SET is_active = 0")
        conn.execute("UPDATE scenarios SET is_active = 1 WHERE id = ?", (scenario_id,))
        conn.commit()


def list_scenarios() -> List[Dict[str, Any]]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT id, name, json, created_ts, is_active FROM scenarios ORDER BY created_ts"
        ).fetchall()
    return [
        {
            "id": row["id"],
            "name": row["name"],
            "scenario": json.loads(row["json"]),
            "created_ts": row["created_ts"],
            "is_active": bool(row["is_active"]),
        }
        for row in rows
    ]
