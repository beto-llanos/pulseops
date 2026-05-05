"""SQLite-backed findings store. Schema is Postgres-compatible."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "pulseops.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    engine TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    annual_cost_usd REAL NOT NULL,
    weekly_cost_usd REAL NOT NULL,
    confidence TEXT NOT NULL,
    suggested_fix TEXT,
    metadata TEXT,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_findings_engine ON findings(engine);
CREATE INDEX IF NOT EXISTS idx_findings_cost ON findings(annual_cost_usd DESC);
"""


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        conn.executescript(SCHEMA)


@contextmanager
def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def insert_finding(
    engine: str,
    title: str,
    description: str,
    annual_cost_usd: float,
    weekly_cost_usd: float,
    confidence: str,
    suggested_fix: str,
    metadata: str = "",
) -> int:
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO findings (engine, title, description, annual_cost_usd,
                weekly_cost_usd, confidence, suggested_fix, metadata, detected_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                engine,
                title,
                description,
                annual_cost_usd,
                weekly_cost_usd,
                confidence,
                suggested_fix,
                metadata,
                datetime.utcnow().isoformat(),
            ),
        )
        return cur.lastrowid
