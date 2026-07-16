"""
Lightweight SQLite persistence layer for prediction history.

Using a real database (instead of an in-memory list) means history
survives app restarts and can scale to many more rows or be swapped
for Postgres/MySQL later with minimal code changes -- only this
module would need to change.
"""

import sqlite3
from contextlib import contextmanager

from config import DB_PATH, HISTORY_DISPLAY_LIMIT


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Create the predictions table if it doesn't exist yet."""
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS predictions (
                id                 INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at         TEXT NOT NULL,
                label              TEXT,
                life_exp           REAL NOT NULL,
                expected_schooling REAL NOT NULL,
                mean_schooling     REAL NOT NULL,
                gni                REAL NOT NULL,
                predicted_hdi      REAL NOT NULL,
                predicted_tier     TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_predictions_created_at "
            "ON predictions (created_at DESC)"
        )


def insert_prediction(label, life_exp, expected_schooling, mean_schooling, gni,
                       predicted_hdi, predicted_tier, created_at):
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO predictions
                (created_at, label, life_exp, expected_schooling,
                 mean_schooling, gni, predicted_hdi, predicted_tier)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (created_at, label, life_exp, expected_schooling,
             mean_schooling, gni, predicted_hdi, predicted_tier),
        )
        return cur.lastrowid


def get_history(limit=HISTORY_DISPLAY_LIMIT):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM predictions ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(row) for row in rows]


def get_history_count():
    with get_connection() as conn:
        row = conn.execute("SELECT COUNT(*) AS c FROM predictions").fetchone()
        return row["c"]


def delete_prediction(record_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM predictions WHERE id = ?", (record_id,))


def clear_history():
    with get_connection() as conn:
        conn.execute("DELETE FROM predictions")
