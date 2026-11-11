import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import backend.config as config
import scripts.run_triage as run_triage


class MockAnswerKeyClient:
    def __init__(self):
        self.prompts = []
        self.payloads = []

    def has_api_key(self):
        return True

    def call_model(self, prompt):
        self.prompts.append(prompt)
        payload = json.loads(prompt.split("INPUT JSON (group_index is the array index):\n", 1)[1])
        self.payloads.append(payload)
        response = []
        for index, group in enumerate(payload):
            if index == 0:
                answer = group["question"]["answer"]
                answer_text = answer if isinstance(answer, str) else json.dumps(answer, ensure_ascii=False)
                response.append({"group_index": index, "verdict": "defect", "repair": "answer_key",
                    "edit": {"field": "answer", "find": answer_text, "replace": "A"},
                    "confidence": 0.99, "evidence": "Mock answer key candidate requiring verification."})
            else:
                response.append({"group_index": index, "verdict": "no_error", "repair": None,
                    "edit": None, "confidence": 0.9, "evidence": "Mocked question analysis."})
        return json.dumps(response)

    @staticmethod
    def extract_json(raw):
        return json.loads(raw)


class GeminiSmokeModeTests(unittest.TestCase):
    def test_real_client_smoke_counts_http_posts_and_never_verifies_with_second_post(self):
        import tempfile
        from scripts.triage.gemini_client import GeminiClient

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            client = GeminiClient(api_key="mock-key", model="mock-model", max_attempts=1)
            requests = []

            def mocked_post(url, **kwargs):
                requests.append((url, kwargs))
                payload = json.loads(kwargs["json"]["contents"][0]["parts"][0]["text"].split(
                    "INPUT JSON (group_index is the array index):\n", 1)[1])
                analyses = []
                for index, group in enumerate(payload):
                    if index == 0:
                        answer = group["question"]["answer"]
                        answer_text = answer if isinstance(answer, str) else json.dumps(answer, ensure_ascii=False)
                        analyses.append({"group_index": index, "verdict": "defect", "repair": "answer_key",
                            "edit": {"field": "answer", "find": answer_text, "replace": "A"},
                            "confidence": 0.99, "evidence": "Mock answer-key candidate."})
                    else:
                        analyses.append({"group_index": index, "verdict": "no_error", "repair": None,
                            "edit": None, "confidence": 0.9, "evidence": "Mocked question analysis."})
                body = {"candidates": [{"content": {"parts": [{"text": json.dumps(analyses)}]}}]}
                return SimpleNamespace(status_code=200, json=lambda: body)

            with patch.object(run_triage, "SMOKE_RESULTS_FILE", root / "smoke.json"), \
                 patch.object(run_triage, "SMOKE_PROGRESS_FILE", root / "progress.json"), \
                 patch("scripts.triage.gemini_client.httpx.post", side_effect=mocked_post):
                results, calls = run_triage.run_smoke_test(client=client)

            self.assertEqual(calls, 1)
            self.assertEqual(len(requests), 1)
            timeout = requests[0][1]["timeout"]
            self.assertEqual(timeout.connect, 15.0)
            self.assertEqual(timeout.read, 120.0)
            self.assertEqual(timeout.write, 30.0)
            self.assertTrue(all(result["route"] == "faculty_review" for result in results
                                if result["repair"] == "answer_key"))

    def test_smoke_transport_failure_does_not_retry_http_post(self):
        import tempfile
        import httpx
        from scripts.triage.gemini_client import GeminiClient

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            calls = []
            def fail_once(*args, **kwargs):
                calls.append(kwargs)
                raise httpx.ReadTimeout("mock read timeout")

            with patch.object(run_triage, "SMOKE_RESULTS_FILE", root / "smoke.json"), \
                 patch.object(run_triage, "SMOKE_PROGRESS_FILE", root / "progress.json"), \
                 patch("scripts.triage.gemini_client.httpx.post", side_effect=fail_once):
                with self.assertRaises(run_triage.SmokeTestRunError) as raised:
                    run_triage.run_smoke_test(client=GeminiClient(api_key="mock-key", max_attempts=5))

            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0]["timeout"].connect, 15.0)
            self.assertEqual(calls[0]["timeout"].read, 120.0)
            self.assertEqual(calls[0]["timeout"].write, 30.0)
            self.assertEqual(raised.exception.api_calls_made, 1)

    def test_smoke_does_not_touch_normal_artifacts_and_skips_verifier(self):
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            smoke_output = root / "gemini_smoke_test.json"
            smoke_progress = root / "gemini_smoke_test_progress.json"
            normal_output = root / "results.json"
            normal_progress = root / "triage_progress.json"
            normal_output.write_text("normal results sentinel", encoding="utf-8")
            normal_progress.write_text("normal progress sentinel", encoding="utf-8")
            client = MockAnswerKeyClient()
            with (
                patch.object(run_triage, "SMOKE_RESULTS_FILE", smoke_output),
                patch.object(run_triage, "SMOKE_PROGRESS_FILE", smoke_progress),
                patch.object(run_triage, "RESULTS_FILE", normal_output),
                patch.object(run_triage, "NORMAL_PROGRESS_FILE", normal_progress),
            ):
                results, calls = run_triage.run_smoke_test(client=client)

            self.assertEqual(calls, 1)
            self.assertEqual(len(client.prompts), 1)
            self.assertEqual(len(client.payloads[0]), config.BATCH_SIZE)
            self.assertFalse(client.prompts[0].startswith("You are an independent Senior"))
            self.assertLess(len(results), 44)
            self.assertTrue(all(result["route"] == "faculty_review"
                                for result in results if result["repair"] == "answer_key"))
            self.assertTrue(smoke_output.exists())
            self.assertEqual(json.loads(smoke_progress.read_text())["api_calls"], 1)
            self.assertEqual(normal_output.read_text(), "normal results sentinel")
            self.assertEqual(normal_progress.read_text(), "normal progress sentinel")
            expected_keys = {"reportId", "questionId", "verdict", "repair", "edit", "route",
                             "confidence", "evidence", "student_reply"}
            self.assertTrue(all(set(result) == expected_keys for result in json.loads(smoke_output.read_text())))

    def test_cli_smoke_branch_prints_details_and_returns_before_normal_flow(self):
        output = io.StringIO()
        with (
            patch.object(sys, "argv", ["run_triage.py", "--smoke-test"]),
            patch.object(run_triage, "run_smoke_test", return_value=([{}], 1)),
            patch.object(run_triage, "prepare_progress", side_effect=AssertionError("normal flow reached")),
            patch.object(run_triage, "GEMINI_MODEL", "mock-model"),
            patch.object(run_triage, "SMOKE_RESULTS_FILE", Path("data/gemini_smoke_test.json")),
            redirect_stdout(output),
        ):
            run_triage.main()
        self.assertIn("1 Gemini API request(s)", output.getvalue())
        self.assertIn("mock-model", output.getvalue())
        self.assertIn("gemini_smoke_test.json", output.getvalue())

    def test_failed_smoke_still_reports_actual_call_count_without_key(self):
        output = io.StringIO()
        error = run_triage.SmokeTestRunError(
            api_calls_made=1, stage="parse response", diagnostic="mock diagnostic"
        )
        with patch.object(sys, "argv", ["run_triage.py", "--smoke-test"]), \
             patch.object(run_triage, "run_smoke_test", side_effect=error), \
             patch.object(run_triage, "GEMINI_MODEL", "mock-model"), \
             patch.object(run_triage, "SMOKE_RESULTS_FILE", Path("data/gemini_smoke_test.json")), \
             redirect_stdout(output), self.assertRaises(SystemExit) as raised:
            run_triage.main()
        self.assertEqual(raised.exception.code, 1)
        self.assertIn("Gemini API requests: 1", output.getvalue())
        self.assertIn("Failure stage: parse response", output.getvalue())
        self.assertIn("Diagnostic: mock diagnostic", output.getvalue())
        self.assertIn("mock-model", output.getvalue())

    def test_missing_api_key_is_a_zero_post_failure_with_clear_diagnostic(self):
        import tempfile
        from scripts.triage.gemini_client import GeminiClient

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(run_triage, "SMOKE_RESULTS_FILE", root / "smoke.json"), \
                 patch.object(run_triage, "SMOKE_PROGRESS_FILE", root / "progress.json"):
                with self.assertRaises(run_triage.SmokeTestRunError) as raised:
                    run_triage.run_smoke_test(client=GeminiClient(api_key="your_gemini_api_key_here"))
        self.assertEqual(raised.exception.api_calls_made, 0)
        self.assertEqual(raised.exception.stage, "validate Gemini API key")
        self.assertIn("GEMINI_API_KEY is missing", raised.exception.diagnostic)

    def test_exhausted_saved_smoke_budget_is_reported_without_post(self):
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            progress = root / "progress.json"
            progress.write_text(json.dumps({"completed": {}, "api_calls": 1,
                                            "verifications": {}, "verification_calls": 0}))
            client = MockAnswerKeyClient()
            with patch.object(run_triage, "SMOKE_RESULTS_FILE", root / "smoke.json"), \
                 patch.object(run_triage, "SMOKE_PROGRESS_FILE", progress):
                with self.assertRaises(run_triage.SmokeTestRunError) as raised:
                    run_triage.run_smoke_test(client=client)
            self.assertEqual(raised.exception.api_calls_made, 0)
            self.assertEqual(raised.exception.stage, "enforce smoke/API request budget")
            self.assertIn("saved count: 1, limit: 1", raised.exception.diagnostic)
            self.assertEqual(progress.read_text(), json.dumps({"completed": {}, "api_calls": 1,
                                                               "verifications": {}, "verification_calls": 0}))

    def test_malformed_saved_progress_is_a_zero_post_local_failure(self):
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            progress = root / "progress.json"
            progress.write_text("{broken", encoding="utf-8")
            with patch.object(run_triage, "SMOKE_RESULTS_FILE", root / "smoke.json"), \
                 patch.object(run_triage, "SMOKE_PROGRESS_FILE", progress):
                with self.assertRaises(run_triage.SmokeTestRunError) as raised:
                    run_triage.run_smoke_test(client=MockAnswerKeyClient())
            self.assertEqual(raised.exception.api_calls_made, 0)
            self.assertEqual(raised.exception.stage, "load and validate saved progress")
            self.assertIn("Invalid JSON", raised.exception.diagnostic)
            self.assertEqual(progress.read_text(encoding="utf-8"), "{broken")

    def test_engine_initialization_failure_is_reported_at_local_setup_stage(self):
        with patch.object(run_triage, "TriageEngine", side_effect=RuntimeError("private details")):
            with self.assertRaises(run_triage.SmokeTestRunError) as raised:
                run_triage.run_smoke_test(client=MockAnswerKeyClient())
        self.assertEqual(raised.exception.api_calls_made, 0)
        self.assertEqual(raised.exception.stage, "initialize engine and load runtime prompts")
        self.assertEqual(raised.exception.diagnostic, "Unexpected RuntimeError; no sensitive exception details were printed.")

    def test_dataset_load_failure_is_reported_before_any_post(self):
        error = FileNotFoundError(2, "missing dataset", "questions.json")
        with patch("builtins.open", side_effect=error):
            with self.assertRaises(run_triage.SmokeTestRunError) as raised:
                run_triage.run_smoke_test(client=MockAnswerKeyClient())
        self.assertEqual(raised.exception.api_calls_made, 0)
        self.assertEqual(raised.exception.stage, "load local question, report, and taxonomy datasets")
        self.assertIn("questions.json", raised.exception.diagnostic)

    def test_request_size_diagnostics_report_safe_counts(self):
        import tempfile

        output = io.StringIO()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(run_triage, "SMOKE_RESULTS_FILE", root / "smoke.json"), \
                 patch.object(run_triage, "SMOKE_PROGRESS_FILE", root / "progress.json"), \
                 redirect_stdout(output):
                run_triage.run_smoke_test(client=MockAnswerKeyClient())
        diagnostic = output.getvalue()
        self.assertRegex(diagnostic, r"\d+ prompt characters; \d+ serialized UTF-8 bytes; 5 question groups; \d+ reports")
        self.assertRegex(diagnostic, r"\d+ question characters; \d+ solution characters")
        self.assertNotIn("reportId", diagnostic)
        self.assertNotIn("questionId", diagnostic)


if __name__ == "__main__":
    unittest.main(verbosity=2)
