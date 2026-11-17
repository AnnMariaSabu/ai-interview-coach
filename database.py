"""
database.py - Save and load interviews with SQLite (a database in one file).
"""
import json
import sqlite3
from datetime import datetime
from pathlib import Path

import config


def connect() -> sqlite3.Connection:
    """Open the database file (it is created automatically the first time)."""
    Path(config.DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(config.DB_PATH)
    connection.row_factory = sqlite3.Row  # lets us read columns by name
    return connection


def create_table():
    """Create the 'interviews' table if it does not exist yet."""
    with connect() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS interviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                candidate_name TEXT,
                job_title TEXT,
                match_score INTEGER,
                overall_score REAL,
                details TEXT
            )
        """)


def answers_to_details(answers: list[dict]) -> list[dict]:
    """Turn the app's answers (with Pydantic forms inside) into plain data that JSON can store."""
    return [
        {
            "question": entry["question"].model_dump(),
            "exchanges": entry["exchanges"],
            "feedback": entry["feedback"].model_dump(),
            "average": entry["average"],
        }
        for entry in answers
    ]


def save_interview(candidate_name: str, job_title: str, match_score: int,
                   overall_score: float, details: list[dict]) -> int:
    """Add one finished interview as a new row. Returns its id number."""
    create_table()
    with connect() as connection:
        cursor = connection.execute(
            "INSERT INTO interviews (date, candidate_name, job_title, match_score, overall_score, details) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                datetime.now().strftime("%Y-%m-%d %H:%M"),
                candidate_name,
                job_title,
                match_score,
                overall_score,
                json.dumps(details),
            ),
        )
        return cursor.lastrowid


def load_interviews() -> list[dict]:
    """Read all saved interviews, oldest first."""
    create_table()
    with connect() as connection:
        rows = connection.execute("SELECT * FROM interviews ORDER BY id").fetchall()

    interviews = []
    for row in rows:
        interview = dict(row)
        interview["details"] = json.loads(interview["details"])  # JSON text -> Python data
        interviews.append(interview)
    return interviews