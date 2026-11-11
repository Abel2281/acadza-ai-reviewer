import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from backend.config import DB_FILE

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_FILE))
    conn.row_factory = sqlite3.Row
    return conn

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
        conn.commit()

def record_audit(
    report_id: str,
    question_id: str,
    action: str,
    faculty_name: Optional[str] = "faculty",
    old_edit: Optional[Any] = None,
    new_edit: Optional[Any] = None,
    reason: Optional[str] = None
) -> int:
    now = datetime.utcnow().isoformat() + "Z"
    old_edit_json = json.dumps(old_edit) if old_edit is not None else None
    new_edit_json = json.dumps(new_edit) if new_edit is not None else None

    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO audit_log (
                report_id, question_id, action, faculty_name,
                old_edit, new_edit, reason, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            report_id, question_id, action, faculty_name,
            old_edit_json, new_edit_json, reason, now
        ))
        conn.commit()
        return cursor.lastrowid

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
