import json
import sqlite3
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).with_name("guardian.db")


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize() -> None:
    with connect() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS cases (
          id INTEGER PRIMARY KEY, case_code TEXT UNIQUE, created_at TEXT NOT NULL,
          risk_score INTEGER NOT NULL, risk_level TEXT NOT NULL, language TEXT NOT NULL,
          indicators TEXT NOT NULL, explanation TEXT NOT NULL, recommended_action TEXT NOT NULL,
          status TEXT NOT NULL, conversation TEXT NOT NULL, timeline TEXT NOT NULL)""")


def serialise(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    for key in ("indicators", "conversation", "timeline"):
        item[key] = json.loads(item[key])
    return item


def create_case(data: dict[str, Any]) -> dict[str, Any]:
    with connect() as conn:
        next_id = conn.execute("SELECT COALESCE(MAX(id), 1046) + 1 FROM cases").fetchone()[0]
        code = f"GA-{next_id}"
        conn.execute("""INSERT INTO cases(case_code,created_at,risk_score,risk_level,language,indicators,explanation,recommended_action,status,conversation,timeline)
        VALUES(?,?,?,?,?,?,?,?,?,?,?)""", (code, data["created_at"], data["risk_score"], data["risk_level"], data["language"], json.dumps(data["indicators"]), data["explanation"], data["recommended_action"], data.get("status", "Reviewing"), json.dumps(data["conversation"]), json.dumps(data.get("timeline", []))))
        return serialise(conn.execute("SELECT * FROM cases WHERE case_code=?", (code,)).fetchone())


def list_cases() -> list[dict[str, Any]]:
    with connect() as conn:
        return [serialise(row) for row in conn.execute("SELECT * FROM cases ORDER BY id DESC")]


def get_case(code: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM cases WHERE case_code=?", (code,)).fetchone()
        return serialise(row) if row else None


def update_case(code: str, status: str) -> dict[str, Any] | None:
    with connect() as conn:
        conn.execute("UPDATE cases SET status=? WHERE case_code=?", (status, code))
    return get_case(code)
