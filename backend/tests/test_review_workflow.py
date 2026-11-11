import tempfile
import unittest
from pathlib import Path

from fastapi import HTTPException
from fastapi import FastAPI
from fastapi.testclient import TestClient

import backend.db as db
from backend.db import get_audit_logs, get_review_statuses, init_db, initialize_pending_statuses
from backend.models import ActionRequest, Edit
from backend.routers.actions import approve_result, edit_and_approve_result, reject_result
from backend.routers.audit import get_all_audit_logs, get_report_audit_logs
from backend.routers.queue import get_queue
from backend.routers.results import get_single_result
from backend.loader import loader


class ReviewWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.previous_db_file = db.DB_FILE
        self.temp_dir = tempfile.TemporaryDirectory()
        db.DB_FILE = Path(self.temp_dir.name) / "audit.db"
        init_db()
        initialize_pending_statuses([report["reportId"] for report in loader.reports_raw])

    def tearDown(self):
        db.DB_FILE = self.previous_db_file
        self.temp_dir.cleanup()

    def question_ids_in_queue(self):
        return {group["questionId"] for group in get_queue()}

    def test_pending_group_appears(self):
        self.assertEqual(len(get_audit_logs()), 0)
        self.assertIn("60f744b3f1b9bc7cc7b4a949", self.question_ids_in_queue())
        self.assertEqual(get_review_statuses()["R001"], "pending")
        self.assertEqual(get_single_result("R001")["result"]["review_status"], "pending")

    def test_approve_removes_group_and_duplicate_reports(self):
        qid = "60f744b3f1b9bc7cc7b4a949"  # R001, R002 and R003
        approve_result("R001", ActionRequest(faculty_name="Faculty A"))
        self.assertNotIn(qid, self.question_ids_in_queue())
        self.assertEqual([get_review_statuses()[rid] for rid in ("R001", "R002", "R003")],
                         ["approved"] * 3)

    def test_resolving_group_from_sibling_report_removes_same_group(self):
        qid = "60f744b3f1b9bc7cc7b4a949"
        approve_result("R002", ActionRequest(faculty_name="Faculty A"))
        self.assertNotIn(qid, self.question_ids_in_queue())
        with self.assertRaises(HTTPException) as raised:
            reject_result("R001", ActionRequest(reason="Cannot reopen"))
        self.assertEqual(raised.exception.status_code, 409)

    def test_edit_and_save_completes_group(self):
        edit_and_approve_result("R004", ActionRequest(
            faculty_name="Faculty B", edit=Edit(field="answer", find="A", replace="D")))
        self.assertNotIn("68e870ef42c06737d6e565c4", self.question_ids_in_queue())
        self.assertEqual(get_review_statuses()["R004"], "edited")

    def test_reject_removes_group(self):
        reject_result("R033", ActionRequest(faculty_name="Faculty C", reason="Verified key"))
        self.assertNotIn("68dea715387eea3d0d95f790", self.question_ids_in_queue())
        self.assertEqual(get_review_statuses()["R033"], "rejected")

    def test_repeated_actions_return_409_without_extra_audit(self):
        approve_result("R001", ActionRequest())
        first_count = len(get_audit_logs())
        for action in (
            lambda: approve_result("R002", ActionRequest()),
            lambda: edit_and_approve_result("R003", ActionRequest(
                edit=Edit(field="answer", find="C", replace="A"))),
            lambda: reject_result("R001", ActionRequest()),
            lambda: edit_and_approve_result("R002", ActionRequest()),
        ):
            with self.assertRaises(HTTPException) as raised:
                action()
            self.assertEqual(raised.exception.status_code, 409)
            self.assertIn("already approved", raised.exception.detail)
        self.assertEqual(len(get_audit_logs()), first_count)

    def test_http_endpoint_returns_409_for_completed_group(self):
        app = FastAPI()
        from backend.routers.actions import router as actions_router
        app.include_router(actions_router)
        client = TestClient(app)
        self.assertEqual(client.post("/api/actions/R001/approve", json={}).status_code, 200)
        response = client.post("/api/actions/R002/reject", json={"reason": "repeat"})
        self.assertEqual(response.status_code, 409)
        self.assertIn("already approved", response.json()["detail"])

    def test_completed_case_cannot_be_reopened_by_another_action(self):
        reject_result("R033", ActionRequest(reason="reviewed"))
        with self.assertRaises(HTTPException) as raised:
            approve_result("R033", ActionRequest())
        self.assertEqual(raised.exception.status_code, 409)
        self.assertEqual(get_review_statuses()["R033"], "rejected")

    def test_audit_history_contains_only_the_real_faculty_actions(self):
        approve_result("R001", ActionRequest(faculty_name="Faculty A", reason="Approved"))
        edit_and_approve_result("R004", ActionRequest(faculty_name="Faculty B",
            edit=Edit(field="answer", find="A", replace="D"), reason="Corrected"))
        reject_result("R033", ActionRequest(faculty_name="Faculty C", reason="Rejected"))
        logs = get_all_audit_logs()
        self.assertEqual({(row["report_id"], row["action"]) for row in logs},
                         {("R001", "approve"), ("R004", "edit"), ("R033", "reject")})
        self.assertEqual(len(get_report_audit_logs("R004")), 1)

    def test_empty_database_initialization_fabricates_no_audit_entries(self):
        db.DB_FILE = Path(self.temp_dir.name) / "empty.db"
        init_db()
        self.assertEqual(get_audit_logs(), [])
        self.assertEqual(get_review_statuses(), {})

    def test_pending_status_seeding_does_not_seed_audit_history(self):
        initialize_pending_statuses(["R001", "R002"])
        statuses = get_review_statuses()
        self.assertEqual(statuses["R001"], "pending")
        self.assertEqual(statuses["R002"], "pending")
        self.assertEqual(get_audit_logs(), [])

    def test_existing_status_table_migrates_without_losing_history(self):
        db.DB_FILE = Path(self.temp_dir.name) / "legacy.db"
        with db.get_connection() as conn:
            conn.execute("""CREATE TABLE review_status (
                report_id TEXT PRIMARY KEY, status TEXT NOT NULL,
                audit_id INTEGER NOT NULL, updated_at TEXT NOT NULL)""")
            conn.execute("INSERT INTO review_status VALUES('R001','approved',4,'2026-01-01T00:00:00Z')")
        init_db()
        initialize_pending_statuses(["R001", "R002"])
        self.assertEqual(get_review_statuses(), {"R001": "approved", "R002": "pending"})

    def test_restart_preserves_status_and_audit_history(self):
        reject_result("R033", ActionRequest(faculty_name="Faculty C", reason="Reviewed"))
        before = get_all_audit_logs()
        init_db()  # Same operation performed when a backend process restarts.
        self.assertEqual(get_review_statuses()["R033"], "rejected")
        self.assertEqual(get_all_audit_logs(), before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
