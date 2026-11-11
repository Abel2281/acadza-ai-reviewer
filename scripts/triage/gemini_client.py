import json
import re
import time
import httpx
from typing import Optional, Dict, Any, List
from backend.config import GEMINI_API_KEY, GEMINI_MODEL

class GeminiQuotaError(RuntimeError):
    """The API rejected the request because its quota is exhausted."""

class GeminiClient:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None,
                 max_attempts: int = 1, timeout=None):
        self.api_key = api_key or GEMINI_API_KEY
        self.model = model or GEMINI_MODEL
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least one")
        self.max_attempts = max_attempts
        # Preserve the normal triage timeout (45 seconds). Smoke mode supplies
        # a phase-specific timeout with a longer read allowance.
        self.timeout = 45.0 if timeout is None else timeout
        self.thinking_level = None
        self.http_posts_made = 0
        self.last_error = None
        self.last_elapsed_seconds = 0.0

    def configure_smoke_test(self) -> None:
        """Set the smoke mode's one-attempt limit and bounded phase timeouts."""
        self.max_attempts = 1
        self.timeout = httpx.Timeout(connect=15.0, read=120.0, write=30.0, pool=15.0)
        self.thinking_level = "low"
        self.http_posts_made = 0
        self.last_error = None
        self.last_elapsed_seconds = 0.0

    def has_api_key(self) -> bool:
        return bool(self.api_key and self.api_key.strip() and self.api_key != "your_gemini_api_key_here")

    def call_model(self, prompt: str, system_instruction: Optional[str] = None) -> Optional[str]:
        if not self.has_api_key():
            return None

        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key,
        }

        contents = [{"parts": [{"text": prompt}]}]
        generation_config: Dict[str, Any] = {"responseMimeType": "application/json"}
        if self.thinking_level:
            generation_config["thinkingConfig"] = {"thinkingLevel": self.thinking_level}
        body: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": generation_config
        }
        if system_instruction:
            body["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        # Each loop iteration issues exactly one HTTP POST. Smoke mode sets this
        # to one so transport failures cannot cause a second request.
        self.last_error = None
        for attempt in range(self.max_attempts):
            started = time.monotonic()
            self.http_posts_made += 1
            try:
                response = httpx.post(
                    self.base_url,
                    json=body,
                    headers=headers,
                    timeout=self.timeout
                )
                self.last_elapsed_seconds = time.monotonic() - started
                if response.status_code == 200:
                    try:
                        data = response.json()
                    except (ValueError, json.JSONDecodeError):
                        self.last_error = "malformed response: body is not valid JSON"
                        print(f"Gemini request failed: {self.last_error}")
                        return None
                    if not isinstance(data, dict):
                        self.last_error = "malformed response: top-level JSON value is not an object"
                        print(f"Gemini request failed: {self.last_error}")
                        return None
                    candidates = data.get("candidates", [])
                    if isinstance(candidates, list) and candidates:
                        first = candidates[0]
                        content = first.get("content") if isinstance(first, dict) else None
                        parts = content.get("parts", []) if isinstance(content, dict) else []
                        text = parts[0].get("text", "") if parts and isinstance(parts[0], dict) else ""
                        if isinstance(text, str) and text:
                            return text
                    self.last_error = "malformed response: candidate text is missing"
                    print(f"Gemini request failed: {self.last_error}")
                    return None
                elif response.status_code == 429:
                    self.last_error = "HTTP status 429 (quota exhausted)"
                    raise GeminiQuotaError(self.last_error)
                else:
                    self.last_error = f"HTTP status {response.status_code}"
                    print(f"Gemini request failed: {self.last_error}")
                    return None
            except GeminiQuotaError:
                raise
            except Exception as e:
                self.last_elapsed_seconds = time.monotonic() - started
                timeout_kinds = (
                    (httpx.ConnectTimeout, "ConnectTimeout"),
                    (httpx.ReadTimeout, "ReadTimeout"),
                    (httpx.WriteTimeout, "WriteTimeout"),
                    (httpx.PoolTimeout, "PoolTimeout"),
                )
                kind = next((label for error_type, label in timeout_kinds
                             if isinstance(e, error_type)), None)
                if kind:
                    self.last_error = f"{kind} after {self.last_elapsed_seconds:.1f}s"
                elif isinstance(e, httpx.TimeoutException):
                    self.last_error = f"TimeoutException after {self.last_elapsed_seconds:.1f}s"
                elif isinstance(e, httpx.TransportError):
                    self.last_error = f"TransportError ({type(e).__name__}) after {self.last_elapsed_seconds:.1f}s"
                else:
                    self.last_error = f"Client error ({type(e).__name__}) after {self.last_elapsed_seconds:.1f}s"
                print(f"Gemini request failed: {self.last_error}")
                return None

        return None

    @staticmethod
    def extract_json(raw_text: str) -> Any:
        if not raw_text:
            return None
        cleaned = raw_text.strip()
        # Remove markdown code blocks if present
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()
        try:
            return json.loads(cleaned)
        except Exception:
            # Try finding first [ or { to last ] or }
            match = re.search(r"(\[.*\]|\{.*\})", cleaned, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except Exception:
                    pass
        return None

