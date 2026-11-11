from typing import Optional, Any, List, Dict
from pydantic import BaseModel, Field

class Edit(BaseModel):
    field: str
    find: Optional[str] = None
    replace: str

class Result(BaseModel):
    reportId: str
    questionId: str
    verdict: str
    repair: Optional[str] = None
    edit: Optional[Edit] = None
    route: str
    confidence: float
    evidence: str
    student_reply: str

class Report(BaseModel):
    reportId: str
    questionId: str
    studentId: str
    source: str
    reportedAt: str
    comment: str

class Question(BaseModel):
    id: str = Field(alias="_id")
    qid: Optional[str] = None
    questionType: str
    subject: str
    chapter: str
    concept: Optional[str] = None
    subConcept: Optional[str] = None
    level: Optional[str] = None
    error: Optional[int] = None
    updatedAt: Optional[str] = None
    scq: Optional[Dict[str, Any]] = None
    integerQuestion: Optional[Dict[str, Any]] = None
    mcq: Optional[Dict[str, Any]] = None
    errorHistory: Optional[List[Dict[str, Any]]] = None

    class Config:
        populate_by_name = True

class ActionRequest(BaseModel):
    faculty_name: Optional[str] = "faculty"
    edit: Optional[Edit] = None
    reason: Optional[str] = None

class AuditEntry(BaseModel):
    id: Optional[int] = None
    report_id: str
    question_id: str
    action: str
    faculty_name: Optional[str] = None
    old_edit: Optional[str] = None
    new_edit: Optional[str] = None
    reason: Optional[str] = None
    created_at: str

