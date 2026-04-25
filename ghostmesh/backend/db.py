import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List

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


def reset_turns() -> None:
    with _conn() as conn:
        conn.execute("DELETE FROM turns")
        conn.commit()
