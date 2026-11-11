import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from backend.config import QUESTIONS_FILE, REPORTS_FILE, TAXONOMY_FILE, RESULTS_FILE
from backend.models import Question, Report, Result

def load_json(path: Path) -> Any:
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

class DataLoader:
    def __init__(self):
        self.questions_raw = load_json(QUESTIONS_FILE) or []
        self.reports_raw = load_json(REPORTS_FILE) or []
        self.taxonomy = load_json(TAXONOMY_FILE) or {}
        self.results_raw = load_json(RESULTS_FILE) or []

        self.questions_by_id: Dict[str, Dict[str, Any]] = {
            q["_id"]: q for q in self.questions_raw
        }
        self.reports_by_id: Dict[str, Dict[str, Any]] = {
            r["reportId"]: r for r in self.reports_raw
        }
        self.reports_by_question: Dict[str, List[Dict[str, Any]]] = {}
        for r in self.reports_raw:
            qid = r["questionId"]
            self.reports_by_question.setdefault(qid, []).append(r)

        self.results_by_id: Dict[str, Dict[str, Any]] = {}
        self.reload_results()

    def reload_results(self):
        self.results_raw = load_json(RESULTS_FILE) or []
        self.results_by_id = {r["reportId"]: r for r in self.results_raw}

    def get_question(self, qid: str) -> Optional[Dict[str, Any]]:
        return self.questions_by_id.get(qid)

    def get_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        return self.reports_by_id.get(report_id)

    def get_result(self, report_id: str) -> Optional[Dict[str, Any]]:
        return self.results_by_id.get(report_id)

    def get_question_content(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """Returns the inner dictionary containing question, solution, and answer."""
        qtype = question.get("questionType", "scq")
        if qtype in question and isinstance(question[qtype], dict):
            return question[qtype]
        for key in ("scq", "integerQuestion", "mcq"):
            if key in question and isinstance(question[key], dict):
                return question[key]
        return {}

# Global loader instance
loader = DataLoader()

