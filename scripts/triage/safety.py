import re
from typing import Dict, Any, Optional, Tuple

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"you\s+are\s+(the\s+)?(admin|system|bot|developer)",
    r"system\s*prompt",
    r"disregard\s+(all\s+)?instructions",
    r"change\s+the\s+answer\s+to\s+[a-d0-9]",
    r"mark\s+this\s+report\s+as\s+corrected",
    r"bypass\s+safety",
]

def is_injection_suspect(comment: str) -> bool:
    if not comment:
        return False
    comment_clean = comment.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, comment_clean):
            return True
    return False

def validate_and_sanitize_result(
    result: Dict[str, Any],
    taxonomy: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Validates taxonomy compliance and enforces safety constraints.
    - Verdict must be in taxonomy['verdicts']
    - If repair is given, must be in taxonomy['repairs']
    - If repair is given, edit.field must be in taxonomy['repairs'][repair]['fields']
    - If repair has auto: false, route MUST be 'faculty_review'
    - Route must be one of: auto_apply, faculty_review, no_change
    """
    verdicts = taxonomy.get("verdicts", {})
    repairs = taxonomy.get("repairs", {})

    verdict = result.get("verdict")
    if verdict not in verdicts:
        # Fallback to not_actionable if hallucinated
        result["verdict"] = "not_actionable"
        result["repair"] = None
        result["edit"] = None
        result["route"] = "no_change"
        result["confidence"] = 0.1
        return result

    repair = result.get("repair")
    edit = result.get("edit")

    # If verdict is not defect, repair and edit must be None
    if verdict != "defect":
        result["repair"] = None
        result["edit"] = None
        result["route"] = "no_change"
        return result

    # Verdict IS defect:
    if repair not in repairs:
        # Invalid repair specified
        result["repair"] = None
        result["edit"] = None
        result["route"] = "faculty_review"
        result["confidence"] = min(result.get("confidence", 0.5), 0.5)
        return result

    repair_def = repairs[repair]
    allowed_fields = repair_def.get("fields", [])
    is_auto_allowed = repair_def.get("auto", False)

    # Check edit field scope
    if edit:
        field = edit.get("field")
        if field not in allowed_fields:
            # Scope violation: strip edit and downgrade
            result["edit"] = None
            result["route"] = "faculty_review"
            result["confidence"] = min(result.get("confidence", 0.5), 0.5)
            result["evidence"] = result.get("evidence", "") + " [Safety: Proposed edit field out of repair scope; escalated to faculty]."
            return result

    # Route assignment enforcement:
    # Rule 7: Never auto-apply repairs marked auto:false
    if not is_auto_allowed:
        result["route"] = "faculty_review"
    else:
        confidence = float(result.get("confidence", 0.0))
        # High-confidence defect with auto:true repair can be auto_apply
        if confidence >= 0.85 and edit is not None:
            result["route"] = "auto_apply"
        else:
            result["route"] = "faculty_review"

    return result

