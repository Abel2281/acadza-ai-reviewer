import json
from pathlib import Path

from scripts.triage.engine import TriageEngine
from scripts.triage.safety import validate_and_sanitize_result


def _data():
    return tuple(json.loads(Path(path).read_text(encoding="utf-8")) for path in (
        "data/questions.json", "data/reports.json", "data/taxonomy.json"))


def test_mock_run_batches_and_resumes_without_live_client(tmp_path):
    questions, reports, taxonomy = _data()
    progress = tmp_path / "progress.json"
    engine = TriageEngine(questions, reports, taxonomy, dry_run=True, progress_path=progress)
    results = engine.process_all_reports()
    assert len(results) == len(reports) == 44
    assert len(json.loads(progress.read_text())["completed"]) == 8
    resumed = TriageEngine(questions, reports, taxonomy, dry_run=True, progress_path=progress)
    assert resumed.process_all_reports() == results
    assert json.loads(progress.read_text())["api_calls"] == 0


def test_taxonomy_semantics_and_unsupported_answer_edit_are_reviewed():
    _, _, taxonomy = _data()
    syllabus = validate_and_sanitize_result({"verdict": "defect", "repair": "syllabus",
        "edit": None, "confidence": 0.99, "evidence": "Curriculum review required."}, taxonomy)
    assert syllabus["verdict"] == "defect"
    assert syllabus["repair"] == "syllabus"
    assert syllabus["route"] == "faculty_review"
    answer_key = validate_and_sanitize_result({"verdict": "defect", "repair": "answer_key",
        "edit": {"field": "answer", "find": "A", "replace": "B"}, "confidence": 0.99,
        "evidence": "Proposed answer change."}, taxonomy)
    assert answer_key["route"] == "faculty_review"


def test_gemini_path_uses_sequential_batches_and_minimal_report_data(tmp_path):
    class MockGeminiClient:
        def __init__(self):
            self.prompts = []

        def has_api_key(self):
            return True

        def call_model(self, prompt):
            self.prompts.append(prompt)
            payload_text = prompt.split("INPUT JSON (group_index is the array index):\n", 1)[1]
            groups = json.loads(payload_text)
            return json.dumps([{"group_index": i, "verdict": "no_error", "repair": None,
                "edit": None, "confidence": 0.9, "evidence": "The stored content was reviewed and no defect was found."}
                for i, _ in enumerate(groups)])

        @staticmethod
        def extract_json(raw):
            return json.loads(raw)

    questions, reports, taxonomy = _data()
    client = MockGeminiClient()
    engine = TriageEngine(questions, reports, taxonomy, client=client, progress_path=tmp_path / "progress.json")
    results = engine.process_all_reports()
    assert len(results) == 44
    assert len(client.prompts) == 8
    assert all("studentId" not in prompt and '"reportId"' not in prompt for prompt in client.prompts)
    assert all("verify_answer" not in prompt for prompt in client.prompts)
    assert json.loads((tmp_path / "progress.json").read_text())["api_calls"] == 8
