from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from backend.loader import loader

router = APIRouter(prefix="/api/results", tags=["results"])

@router.get("", response_model=List[Dict[str, Any]])
def get_all_results():
    loader.reload_results()
    return loader.results_raw

@router.get("/{report_id}")
def get_single_result(report_id: str):
    loader.reload_results()
    res = loader.get_result(report_id)
    if not res:
        raise HTTPException(status_code=404, detail=f"Result with reportId {report_id} not found")

    report = loader.get_report(report_id)
    question = loader.get_question(res["questionId"])
    content = loader.get_question_content(question) if question else {}

    # Get sibling reports for this question
    siblings = [
        loader.get_result(r["reportId"])
        for r in loader.reports_by_question.get(res["questionId"], [])
        if r["reportId"] != report_id
    ]

    return {
        "result": res,
        "report": report,
        "question": question,
        "question_content": content,
        "sibling_results": [s for s in siblings if s]
    }
