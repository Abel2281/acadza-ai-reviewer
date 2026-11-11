from fastapi import APIRouter, HTTPException

from backend.db import InvalidReviewAction, ReviewAlreadyResolved, record_group_action
from backend.loader import loader
from backend.models import ActionRequest

router = APIRouter(prefix="/api/actions", tags=["actions"])


def _record_action(report_id: str, req: ActionRequest, action: str, new_edit=None):
    loader.reload_results()
    result = loader.get_result(report_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")

    question_id = result["questionId"]
    group_report_ids = [
        report["reportId"]
        for report in loader.reports_by_question.get(question_id, [])
    ] or [report_id]
    try:
        audit_id = record_group_action(
            report_ids=group_report_ids,
            report_id=report_id,
            question_id=question_id,
            action=action,
            faculty_name=req.faculty_name or "faculty",
            old_edit=result.get("edit"),
            new_edit=new_edit if action == "edited" else result.get("edit") if action == "approved" else None,
            reason=req.reason or ("Rejected by faculty" if action == "rejected" else None),
        )
    except ReviewAlreadyResolved as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except InvalidReviewAction as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result, audit_id


@router.post("/{report_id}/approve")
def approve_result(report_id: str, req: ActionRequest):
    result, audit_id = _record_action(report_id, req, "approved")
    return {
        "status": "approved",
        "reportId": report_id,
        "audit_id": audit_id,
        "message": f"Proposal for {report_id} approved by {req.faculty_name or 'faculty'}.",
    }


@router.post("/{report_id}/edit")
def edit_and_approve_result(report_id: str, req: ActionRequest):
    edit = req.edit.model_dump() if req.edit else None
    _, audit_id = _record_action(report_id, req, "edited", edit)
    return {
        "status": "edited",
        "reportId": report_id,
        "audit_id": audit_id,
        "new_edit": edit,
        "message": f"Correction for {report_id} modified and approved by {req.faculty_name or 'faculty'}.",
    }


@router.post("/{report_id}/reject")
def reject_result(report_id: str, req: ActionRequest):
    _, audit_id = _record_action(report_id, req, "rejected")
    return {
        "status": "rejected",
        "reportId": report_id,
        "audit_id": audit_id,
        "reason": req.reason,
        "message": f"Proposal for {report_id} rejected by {req.faculty_name or 'faculty'}.",
    }
