import json
import re
from pathlib import Path

from scripts.triage.engine import TriageEngine
from scripts.triage.safety import validate_and_sanitize_result
from scripts.triage.engine import REDACTED_COMMENT
from scripts.run_triage import prepare_progress


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


def test_r027_comment_is_redacted_but_its_question_is_still_analyzed(tmp_path):
    class MockGeminiClient:
        def __init__(self):
            self.prompts = []

        def has_api_key(self):
            return True

        def call_model(self, prompt):
            self.prompts.append(prompt)
            groups = json.loads(prompt.split("INPUT JSON (group_index is the array index):\n", 1)[1])
            return json.dumps([{"group_index": i, "verdict": "no_error", "repair": None,
                "edit": None, "confidence": 0.9, "evidence": "The question was analyzed and no defect was found."}
                for i, _ in enumerate(groups)])

        @staticmethod
        def extract_json(raw):
            return json.loads(raw)

    questions, reports, taxonomy = _data()
    r027 = next(report for report in reports if report["reportId"] == "R027")
    question = next(item for item in questions if item["_id"] == r027["questionId"])
    question_text = question[question["questionType"]]["question"]
    client = MockGeminiClient()
    results = TriageEngine(questions, reports, taxonomy, client=client,
        progress_path=tmp_path / "progress.json").process_all_reports()
    target_prompt = next(prompt for prompt in client.prompts if REDACTED_COMMENT in prompt)
    assert r027["comment"] not in target_prompt
    payload = json.loads(target_prompt.split("INPUT JSON (group_index is the array index):\n", 1)[1])
    assert any(group["question"]["question"] == question_text for group in payload)
    assert next(result for result in results if result["reportId"] == "R027")["verdict"] == "not_actionable"


def test_separate_answer_verification_uses_two_calls_within_ten_call_limit(tmp_path):
    class MockGeminiClient:
        def __init__(self):
            self.prompts = []

        def has_api_key(self):
            return True

        def call_model(self, prompt):
            self.prompts.append(prompt)
            if prompt.startswith("You are an independent Senior"):
                return json.dumps({"verified": True, "derived_answer": "A",
                    "step_by_step_proof": "Independent derivation supports the proposed value.", "confidence": 0.95})
            groups = json.loads(prompt.split("INPUT JSON (group_index is the array index):\n", 1)[1])
            answers = []
            for i, group in enumerate(groups):
                answer = group["question"]["answer"]
                answer_text = answer if isinstance(answer, str) else json.dumps(answer, ensure_ascii=False)
                if i < 2 and len(self.prompts) == 1:
                    answers.append({"group_index": i, "verdict": "defect", "repair": "answer_key",
                        "edit": {"field": "answer", "find": answer_text, "replace": "A"},
                        "confidence": 0.97, "evidence": "A separate check is requested for the answer key."})
                else:
                    answers.append({"group_index": i, "verdict": "no_error", "repair": None,
                        "edit": None, "confidence": 0.9, "evidence": "The question was checked."})
            return json.dumps(answers)

        @staticmethod
        def extract_json(raw):
            return json.loads(raw)

    questions, reports, taxonomy = _data()
    client = MockGeminiClient()
    progress = tmp_path / "progress.json"
    results = TriageEngine(questions, reports, taxonomy, client=client,
        progress_path=progress).process_all_reports()
    saved = json.loads(progress.read_text())
    assert len(client.prompts) == 10
    assert saved["api_calls"] == 10
    assert saved["verification_calls"] == 2
    assert sum(prompt.startswith("You are an independent Senior") for prompt in client.prompts) == 2
    assert len(results) == 44

    exhausted = tmp_path / "exhausted.json"
    exhausted.write_text(json.dumps({"completed": {}, "api_calls": 10}))
    blocked_client = MockGeminiClient()
    try:
        TriageEngine(questions, reports, taxonomy, client=blocked_client,
            progress_path=exhausted).process_all_reports()
        raise AssertionError("A run at the call limit must stop before another request")
    except RuntimeError as exc:
        assert "API call limit" in str(exc)
    assert blocked_client.prompts == []


def test_resume_requires_explicit_choice_before_discarding_progress(tmp_path):
    progress = tmp_path / "triage_progress.json"
    progress.write_text('{"saved":"keep me"}')
    try:
        prepare_progress(progress, resume=False, fresh_run=False)
        raise AssertionError("Existing progress must require an explicit choice")
    except FileExistsError:
        pass
    assert progress.read_text() == '{"saved":"keep me"}'
    prepare_progress(progress, resume=True, fresh_run=False)
    assert progress.exists()
    prepare_progress(progress, resume=False, fresh_run=True)
    assert not progress.exists()


def test_engine_malformed_confidence_never_crashes_or_auto_applies(tmp_path):
    questions, reports, taxonomy = _data()
    report = reports[0]
    question = next(item for item in questions if item["_id"] == report["questionId"])
    question_text = question[question["questionType"]]["question"]

    class MockGeminiClient:
        def __init__(self, confidence, omit_confidence=False):
            self.confidence = confidence
            self.omit_confidence = omit_confidence

        def has_api_key(self):
            return True

        def call_model(self, prompt):
            result = {"group_index": 0, "verdict": "defect", "repair": "spelling",
                "edit": {"field": "question", "find": question_text[:8], "replace": question_text[:8] + "!"},
                "evidence": "A mocked correction proposal."}
            if not self.omit_confidence:
                result["confidence"] = self.confidence
            return json.dumps([result])

        @staticmethod
        def extract_json(raw):
            return json.loads(raw)

    cases = [(value, False) for value in (None, "0.99", True, float("nan"), float("inf"), -0.1, 1.1)]
    cases.append((None, True))
    for index, (confidence, omit_confidence) in enumerate(cases):
        result = TriageEngine([question], [report], taxonomy,
            client=MockGeminiClient(confidence, omit_confidence),
            progress_path=tmp_path / f"{index}.json").process_all_reports()[0]
        assert result["route"] == "faculty_review"
        assert result["confidence"] == 0.0
        assert result["edit"] is None


def test_engine_malformed_verification_confidence_never_auto_applies(tmp_path):
    questions, reports, taxonomy = _data()
    report = reports[0]
    question = next(item for item in questions if item["_id"] == report["questionId"])
    answer = question[question["questionType"]]["answer"]
    answer_text = answer if isinstance(answer, str) else json.dumps(answer, ensure_ascii=False)

    class MockGeminiClient:
        def __init__(self, verification_confidence, omit_confidence=False):
            self.verification_confidence = verification_confidence
            self.omit_confidence = omit_confidence

        def has_api_key(self):
            return True

        def call_model(self, prompt):
            if prompt.startswith("You are an independent Senior"):
                verification = {"verified": True, "derived_answer": "A",
                    "step_by_step_proof": "Mocked separate verification."}
                if not self.omit_confidence:
                    verification["confidence"] = self.verification_confidence
                return json.dumps(verification)
            return json.dumps([{"group_index": 0, "verdict": "defect", "repair": "answer_key",
                "edit": {"field": "answer", "find": answer_text, "replace": "A"},
                "confidence": 0.99, "evidence": "Mocked answer-key proposal."}])

        @staticmethod
        def extract_json(raw):
            return json.loads(raw)

    invalid_values = [None, "0.99", True, float("nan"), float("inf"), float("-inf"), -0.1, 1.1]
    cases = [(value, False) for value in invalid_values]
    cases.append((None, True))
    for index, (confidence, omit_confidence) in enumerate(cases):
        result = TriageEngine([question], [report], taxonomy,
            client=MockGeminiClient(confidence, omit_confidence),
            progress_path=tmp_path / f"verification-{index}.json").process_all_reports()[0]
        assert result["route"] == "faculty_review"


def test_batch_prompt_taxonomy_matches_taxonomy_json():
    _, _, taxonomy = _data()
    prompt = Path("scripts/triage/prompts/batch_triage.txt").read_text(encoding="utf-8")
    verdict_section = re.search(r"2\. Verdicts.*?closed list:\n(.*?)\n\n3\.", prompt, re.S).group(1)
    prompt_verdicts = {
        name: description.strip()
        for name, description in re.findall(r"^\s*-\s*([a-z_]+):\s*(.+)$", verdict_section, re.M)
    }
    repair_section = re.search(r"3\. Repair types.*?closed list:\n(.*?)\n\n4\.", prompt, re.S).group(1)
    prompt_repairs = {
        name: (json.loads(fields), automation == "true")
        for name, fields, automation in re.findall(
            r"^\s*-\s*([a-z_]+)\s*\(fields:\s*(\[[^\]]*\]),\s*auto:\s*(true|false)\):",
            repair_section, re.M,
        )
    }
    assert prompt_verdicts == taxonomy["verdicts"]
    assert set(prompt_repairs) == set(taxonomy["repairs"])
    assert prompt_repairs == {
        name: (definition["fields"], definition["auto"])
        for name, definition in taxonomy["repairs"].items()
    }
