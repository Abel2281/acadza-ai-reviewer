import re
from fastapi import APIRouter
from typing import List, Dict, Any
from backend.loader import loader
from backend.db import get_review_statuses

router = APIRouter(prefix="/api/queue", tags=["queue"])

def strip_html(text: str) -> str:
    if not text:
        return ""
    clean = re.sub(r"<[^>]+>", " ", text)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean

@router.get("")
def get_queue():
    loader.reload_results()
    review_statuses = get_review_statuses()
    groups: Dict[str, Dict[str, Any]] = {}

    for r in loader.reports_raw:
        qid = r["questionId"]
        report_id = r["reportId"]
        result = loader.get_result(report_id) or {}
        question = loader.get_question(qid) or {}
        content = loader.get_question_content(question)

        if qid not in groups:
            q_text_plain = strip_html(content.get("question", ""))
            groups[qid] = {
                "questionId": qid,
                "subject": question.get("subject", "Unknown"),
                "chapter": question.get("chapter", "Unknown"),
                "questionType": question.get("questionType", "scq"),
                "question_preview": q_text_plain[:180] + ("..." if len(q_text_plain) > 180 else ""),
                "reports": [],
                "results": [],
                "urgency_score": 0,
                "report_count": 0,
                "max_confidence": 0.0,
                "top_verdict": "no_error",
                "top_route": "no_change",
                "repairs": []
            }

        groups[qid]["reports"].append(r)
        groups[qid]["results"].append({**result, "review_status": review_statuses.get(report_id, "pending")})
        groups[qid]["report_count"] += 1

    # Compute urgency score and summary indicators for each group
    group_list = []
    verdict_weights = {
        "defect": 100,
        "display_issue": 40,
        "app_issue": 30,
        "language_mode": 15,
        "syllabus": 25,
        "not_actionable": 5,
        "already_fixed": 10,
        "no_error": 10
    }

    for qid, g in groups.items():
        max_v_weight = 0
        top_v = "no_error"
        top_route = "no_change"
        max_conf = 0.0
        repairs_set = set()

        for res in g["results"]:
            v = res.get("verdict", "no_error")
            w = verdict_weights.get(v, 10)
            if w > max_v_weight:
                max_v_weight = w
                top_v = v
                top_route = res.get("route", "no_change")
            conf = float(res.get("confidence", 0.0))
            if conf > max_conf:
                max_conf = conf
            rep = res.get("repair")
            if rep:
                repairs_set.add(rep)

        # Urgency formula: base weight + report count multiplier + confidence bonus
        urgency = max_v_weight + (g["report_count"] * 15) + int(max_conf * 10)

        g["urgency_score"] = urgency
        g["top_verdict"] = top_v
        g["top_route"] = top_route
        g["max_confidence"] = round(max_conf, 2)
        g["repairs"] = list(repairs_set)
        group_list.append(g)

    # Sort descending by urgency score
    group_list.sort(key=lambda x: x["urgency_score"], reverse=True)
    return group_list
