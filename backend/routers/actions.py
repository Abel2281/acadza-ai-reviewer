from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
from backend.models import ActionRequest
from backend.loader import loader
from backend.db import record_audit, set_review_status

router = APIRouter(prefix="/api/actions", tags=["actions"])

@router.post("/{report_id}/approve")
def approve_result(report_id: str, req: ActionRequest):
    loader.reload_results()
    res = loader.get_result(report_id)
    if not res:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")

    old_edit = res.get("edit")
    audit_id = record_audit(
        report_id=report_id,
        question_id=res["questionId"],
        action="approve",
        faculty_name=req.faculty_name or "faculty",
        old_edit=old_edit,
        new_edit=old_edit,
        reason=req.reason
    )
    set_review_status(report_id, "approved", audit_id)

    return {
        "status": "approved",
        "reportId": report_id,
        "audit_id": audit_id,
        "message": f"Proposal for {report_id} approved by {req.faculty_name or 'faculty'}."
    }

@router.post("/{report_id}/edit")
def edit_and_approve_result(report_id: str, req: ActionRequest):
    loader.reload_results()
    res = loader.get_result(report_id)
    if not res:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")

    if not req.edit:
        raise HTTPException(status_code=400, detail="Edited correction data is required")

    old_edit = res.get("edit")
    new_edit_dict = req.edit.dict()

    audit_id = record_audit(
        report_id=report_id,
        question_id=res["questionId"],
        action="edit",
        faculty_name=req.faculty_name or "faculty",
        old_edit=old_edit,
        new_edit=new_edit_dict,
        reason=req.reason
    )
    set_review_status(report_id, "edited", audit_id)

    return {
        "status": "edited",
        "reportId": report_id,
        "audit_id": audit_id,
        "new_edit": new_edit_dict,
        "message": f"Correction for {report_id} modified and approved by {req.faculty_name or 'faculty'}."
    }

@router.post("/{report_id}/reject")
def reject_result(report_id: str, req: ActionRequest):
    loader.reload_results()
    res = loader.get_result(report_id)
    if not res:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")

    old_edit = res.get("edit")
    audit_id = record_audit(
        report_id=report_id,
        question_id=res["questionId"],
        action="reject",
        faculty_name=req.faculty_name or "faculty",
        old_edit=old_edit,
        new_edit=None,
        reason=req.reason or "Rejected by faculty"
    )
    set_review_status(report_id, "rejected", audit_id)

    return {
        "status": "rejected",
        "reportId": report_id,
        "audit_id": audit_id,
        "reason": req.reason,
        "message": f"Proposal for {report_id} rejected by {req.faculty_name or 'faculty'}."
    }
