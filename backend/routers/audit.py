from fastapi import APIRouter, Query
from typing import List, Dict, Any, Optional
from backend.db import get_audit_logs

router = APIRouter(prefix="/api/audit", tags=["audit"])

@router.get("", response_model=List[Dict[str, Any]])
def get_all_audit_logs(
    limit: int = 50,
    offset: int = 0
):
    return get_audit_logs(limit=limit, offset=offset)

@router.get("/{report_id}", response_model=List[Dict[str, Any]])
def get_report_audit_logs(
    report_id: str,
    limit: int = 20,
    offset: int = 0
):
    return get_audit_logs(report_id=report_id, limit=limit, offset=offset)
