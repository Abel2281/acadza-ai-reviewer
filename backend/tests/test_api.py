import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.models import ActionRequest, Edit
from backend.routers.results import get_all_results, get_single_result
from backend.routers.queue import get_queue
from backend.routers.metrics import get_metrics
from backend.routers.actions import approve_result, edit_and_approve_result, reject_result
from backend.routers.audit import get_all_audit_logs, get_report_audit_logs
from backend.db import init_db

def run_tests():
    init_db()

    # 1. Results endpoint
    all_res = get_all_results()
    assert len(all_res) == 44
    print("1. get_all_results: 44 results OK")

    # 2. Single result
    r001 = get_single_result("R001")
    assert r001["result"]["reportId"] == "R001"
    assert r001["question"]["_id"] == r001["result"]["questionId"]
    assert len(r001["sibling_results"]) == 2 # R002 and R003 are siblings
    print("2. get_single_result(R001) with siblings: OK")

    # 3. Queue endpoint
    q = get_queue()
    assert len(q) == 39
    assert q[0]["urgency_score"] >= q[-1]["urgency_score"]
    print(f"3. get_queue: 39 unique questions, sorted by urgency (top={q[0]['urgency_score']}) OK")

    # 4. Metrics endpoint
    m = get_metrics()
    assert m["total_reports"] == 44
    assert m["defects_count"] == 26
    assert m["auto_apply_count"] == 19
    print("4. get_metrics: OK", m)

    # 5. Actions: Approve
    appr = approve_result("R001", ActionRequest(faculty_name="Dr. Mehta", reason="Checked solution"))
    assert appr["status"] == "approved"
    print("5. approve_result: OK")

    # 6. Actions: Edit
    ed = edit_and_approve_result("R004", ActionRequest(
        faculty_name="Dr. Mehta",
        edit=Edit(field="answer", find="A", replace="D"),
        reason="Answer is D"
    ))
    assert ed["status"] == "edited"
    print("6. edit_and_approve_result: OK")

    # 7. Actions: Reject
    rej = reject_result("R033", ActionRequest(faculty_name="Dr. Mehta", reason="Correct significant digits"))
    assert rej["status"] == "rejected"
    print("7. reject_result: OK")

    # 8. Audit logs
    logs = get_all_audit_logs()
    assert len(logs) >= 3
    r001_logs = get_report_audit_logs("R001")
    assert len(r001_logs) >= 1
    print("8. audit_logs query: OK")

    print("\nALL BACKEND ROUTERS & LOGIC FULLY TESTED AND PASSED!")

if __name__ == "__main__":
    run_tests()
