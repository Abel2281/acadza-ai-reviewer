import sqlite3
import json
from contextlib import contextmanager
from datetime import datetime
from typing import List, Dict, Any, Optional
from backend.config import DB_FILE

TERMINAL_REVIEW_STATUSES = frozenset({"approved", "edited", "rejected"})


class ReviewAlreadyResolved(Exception):
    pass


class InvalidReviewAction(Exception):
    pass

@contextmanager
def get_connection():
    conn = sqlite3.connect(str(DB_FILE))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id    TEXT NOT NULL,
                question_id  TEXT NOT NULL,
                action       TEXT NOT NULL,
                faculty_name TEXT,
                old_edit     TEXT,
                new_edit     TEXT,
                reason       TEXT,
                created_at   TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS review_status (
                report_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                audit_id INTEGER,
                updated_at TEXT NOT NULL
            )
        """)
        status_columns = {row["name"]: row for row in conn.execute("PRAGMA table_info(review_status)")}
        if status_columns["audit_id"]["notnull"]:
            conn.execute("ALTER TABLE review_status RENAME TO review_status_legacy")
            conn.execute("""CREATE TABLE review_status (
                report_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                audit_id INTEGER,
                updated_at TEXT NOT NULL
            )""")
            conn.execute("""INSERT INTO review_status(report_id,status,audit_id,updated_at)
                SELECT report_id,status,audit_id,updated_at FROM review_status_legacy""")
            conn.execute("DROP TABLE review_status_legacy")
        conn.commit()


def initialize_pending_statuses(report_ids: List[str]) -> None:
    """Persist initial pending state without creating any audit history."""
    now = datetime.utcnow().isoformat() + "Z"
    with get_connection() as conn:
        conn.executemany(
            "INSERT OR IGNORE INTO review_status(report_id,status,audit_id,updated_at) VALUES(?, 'pending', NULL, ?)",
            [(report_id, now) for report_id in dict.fromkeys(report_ids)],
        )

def record_group_action(
    report_ids: List[str],
    report_id: str,
    question_id: str,
    action: str,
    faculty_name: Optional[str] = "faculty",
    old_edit: Optional[Any] = None,
    new_edit: Optional[Any] = None,
    reason: Optional[str] = None,
) -> int:
    """Atomically add one real faculty action and resolve every report in its question group."""
    if action not in TERMINAL_REVIEW_STATUSES:
        raise ValueError(f"Unsupported terminal review action: {action}")
    audit_action = {"approved": "approve", "edited": "edit", "rejected": "reject"}[action]
    unique_report_ids = list(dict.fromkeys(report_ids))
    placeholders = ",".join("?" for _ in unique_report_ids)
    now = datetime.utcnow().isoformat() + "Z"
    with get_connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        if placeholders:
            resolved = conn.execute(
                f"SELECT report_id, status FROM review_status WHERE report_id IN ({placeholders})",
                unique_report_ids,
            ).fetchall()
            already_resolved = next(
                (row for row in resolved if row["status"] in TERMINAL_REVIEW_STATUSES), None
            )
            if already_resolved:
                raise ReviewAlreadyResolved(
                    f"Question group {question_id} is already {already_resolved['status']}; "
                    "completed cases cannot be changed again."
                )
        if action == "edited" and new_edit is None:
            raise InvalidReviewAction("Edited correction data is required")

        cursor = conn.execute(
            """INSERT INTO audit_log (
                report_id, question_id, action, faculty_name,
                old_edit, new_edit, reason, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (report_id, question_id, audit_action, faculty_name,
             json.dumps(old_edit) if old_edit is not None else None,
             json.dumps(new_edit) if new_edit is not None else None,
             reason, now),
        )
        audit_id = cursor.lastrowid
        conn.executemany(
            """INSERT INTO review_status(report_id,status,audit_id,updated_at)
               VALUES(?,?,?,?) ON CONFLICT(report_id) DO UPDATE SET
               status=excluded.status,audit_id=excluded.audit_id,updated_at=excluded.updated_at""",
            [(group_report_id, action, audit_id, now) for group_report_id in unique_report_ids],
        )
        conn.commit()
        return audit_id

def get_audit_logs(report_id: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        if report_id:
            cursor = conn.execute("""
                SELECT * FROM audit_log
                WHERE report_id = ?
                ORDER BY id DESC
                LIMIT ? OFFSET ?
            """, (report_id, limit, offset))
        else:
            cursor = conn.execute("""
                SELECT * FROM audit_log
                ORDER BY id DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def get_review_statuses() -> Dict[str, str]:
    with get_connection() as conn:
        return {row["report_id"]: row["status"] for row in conn.execute("SELECT report_id,status FROM review_status")}
