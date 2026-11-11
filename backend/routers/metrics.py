from fastapi import APIRouter
from typing import Dict, Any
from backend.loader import loader

router = APIRouter(prefix="/api/metrics", tags=["metrics"])

@router.get("")
def get_metrics() -> Dict[str, Any]:
    loader.reload_results()

    total_reports = len(loader.reports_raw)
    total_questions = len(loader.questions_raw)

    by_verdict = {}
    by_route = {}
    by_repair = {}
    by_subject = {}

    for res in loader.results_raw:
        v = res.get("verdict", "unknown")
        by_verdict[v] = by_verdict.get(v, 0) + 1

        route = res.get("route", "unknown")
        by_route[route] = by_route.get(route, 0) + 1

        rep = res.get("repair")
        if rep:
            by_repair[rep] = by_repair.get(rep, 0) + 1

        qid = res.get("questionId")
        q = loader.get_question(qid)
        if q:
            subj = q.get("subject", "Unknown")
            by_subject[subj] = by_subject.get(subj, 0) + 1

    return {
        "total_reports": total_reports,
        "total_questions": total_questions,
        "defects_count": by_verdict.get("defect", 0),
        "auto_apply_count": by_route.get("auto_apply", 0),
        "faculty_review_count": by_route.get("faculty_review", 0),
        "no_change_count": by_route.get("no_change", 0),
        "by_verdict": by_verdict,
        "by_route": by_route,
        "by_repair": by_repair,
        "by_subject": by_subject
    }
