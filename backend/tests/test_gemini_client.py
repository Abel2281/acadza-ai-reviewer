import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch
from unittest import mock

from scripts.triage.gemini_client import GeminiClient


class GeminiClientTests(unittest.TestCase):
    def test_key_is_sent_only_in_header_and_json_mode_has_no_sampling_parameters(self):
        key = "private-test-key-123"
        client = GeminiClient(api_key=key, model="gemini-test")
        response = mock.Mock()
        response.status_code = 200
        response.json.return_value = {"candidates": [{"content": {"parts": [{"text": "{}"}]}}]}
        with patch("scripts.triage.gemini_client.httpx.post", return_value=response) as post:
            self.assertEqual(client.call_model("prompt"), "{}")
        args, kwargs = post.call_args
        self.assertNotIn(key, args[0])
        self.assertNotIn("?", args[0])
        self.assertNotIn("params", kwargs)
        self.assertNotIn("temperature", kwargs)
        self.assertEqual(kwargs["timeout"], 45.0)
        self.assertEqual(kwargs["headers"]["x-goog-api-key"], key)
        self.assertEqual(kwargs["json"]["generationConfig"], {"responseMimeType": "application/json"})

    def test_response_errors_never_print_api_key_or_response_body(self):
        key = "private-test-key-456"
        client = GeminiClient(api_key=key, model="gemini-test")
        response = mock.Mock(status_code=500, text=f"server echoed {key}")
        output = io.StringIO()
        with patch("scripts.triage.gemini_client.httpx.post", return_value=response), redirect_stdout(output):
            self.assertIsNone(client.call_model("prompt"))
        self.assertNotIn(key, output.getvalue())

    def test_transport_error_redacts_api_key(self):
        key = "private-test-key-789"
        client = GeminiClient(api_key=key, model="gemini-test")
        output = io.StringIO()
        with patch("scripts.triage.gemini_client.httpx.post", side_effect=RuntimeError(f"failure {key}")), redirect_stdout(output):
            self.assertIsNone(client.call_model("prompt"))
        self.assertNotIn(key, output.getvalue())
        self.assertIn("Client error (RuntimeError)", output.getvalue())

    def test_read_timeout_is_configured_for_smoke_and_only_one_post_is_attempted(self):
        import httpx

        client = GeminiClient(api_key="mock-key", max_attempts=5)
        client.configure_smoke_test()
        calls = []

        def timeout(*args, **kwargs):
            calls.append(kwargs)
            raise httpx.ReadTimeout("mock read timeout")

        with patch("scripts.triage.gemini_client.httpx.post", side_effect=timeout):
            self.assertIsNone(client.call_model("prompt"))

        self.assertEqual(len(calls), 1)
        self.assertEqual(client.max_attempts, 1)
        self.assertEqual(calls[0]["timeout"].connect, 15.0)
        self.assertEqual(calls[0]["timeout"].read, 120.0)
        self.assertEqual(calls[0]["timeout"].write, 30.0)
        self.assertEqual(client.last_error.split(" after ")[0], "ReadTimeout")
        self.assertGreaterEqual(client.last_elapsed_seconds, 0)

    def test_smoke_timeout_types_are_classified_without_retry(self):
        import httpx

        timeout_cases = (
            (httpx.ConnectTimeout, "ConnectTimeout"),
            (httpx.ReadTimeout, "ReadTimeout"),
            (httpx.WriteTimeout, "WriteTimeout"),
            (httpx.PoolTimeout, "PoolTimeout"),
        )
        for exception_type, label in timeout_cases:
            with self.subTest(timeout=label):
                client = GeminiClient(api_key="mock-key")
                client.configure_smoke_test()
                posts = []
                def fail(*args, **kwargs):
                    posts.append(kwargs)
                    raise exception_type("mock timeout")
                with patch("scripts.triage.gemini_client.httpx.post", side_effect=fail):
                    self.assertIsNone(client.call_model("mock prompt"))
                self.assertEqual(len(posts), 1)
                self.assertTrue(client.last_error.startswith(label + " after "))

    def test_http_status_and_malformed_response_are_distinguished(self):
        client = GeminiClient(api_key="mock-key")
        response = mock.Mock(status_code=503)
        with patch("scripts.triage.gemini_client.httpx.post", return_value=response):
            self.assertIsNone(client.call_model("mock prompt"))
        self.assertEqual(client.last_error, "HTTP status 503")

        response = mock.Mock(status_code=200)
        response.json.return_value = {"candidates": []}
        with patch("scripts.triage.gemini_client.httpx.post", return_value=response):
            self.assertIsNone(client.call_model("mock prompt"))
        self.assertIn("malformed response", client.last_error)

    def test_smoke_generation_config_uses_supported_low_thinking_level(self):
        client = GeminiClient(api_key="mock-key")
        client.configure_smoke_test()
        response = mock.Mock(status_code=200)
        response.json.return_value = {"candidates": [{"content": {"parts": [{"text": "[]"}]}}]}
        with patch("scripts.triage.gemini_client.httpx.post", return_value=response) as post:
            client.call_model("mock prompt")
        self.assertEqual(post.call_args.kwargs["json"]["generationConfig"], {
            "responseMimeType": "application/json",
            "thinkingConfig": {"thinkingLevel": "low"},
        })


if __name__ == "__main__":
    unittest.main(verbosity=2)
