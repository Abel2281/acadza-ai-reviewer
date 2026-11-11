import json
import re
import time
import httpx
from typing import Optional, Dict, Any, List
from backend.config import GEMINI_API_KEY, GEMINI_MODEL

class GeminiClient:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or GEMINI_API_KEY
        self.model = model or GEMINI_MODEL
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

    def has_api_key(self) -> bool:
        return bool(self.api_key and self.api_key.strip() and self.api_key != "your_gemini_api_key_here")

    def call_model(self, prompt: str, system_instruction: Optional[str] = None, temperature: float = 0.1) -> Optional[str]:
        if not self.has_api_key():
            return None

        headers = {"Content-Type": "application/json"}
        params = {"key": self.api_key}

        contents = [{"parts": [{"text": prompt}]}]
        body: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "responseMimeType": "application/json"
            }
        }
        if system_instruction:
            body["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = httpx.post(
                    self.base_url,
                    params=params,
                    json=body,
                    headers=headers,
                    timeout=45.0
                )
                if response.status_code == 200:
                    data = response.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        return text
                elif response.status_code == 429:
                    wait_time = (attempt + 1) * 3
                    time.sleep(wait_time)
                else:
                    print(f"Gemini API returned status {response.status_code}: {response.text}")
                    return None
            except Exception as e:
                print(f"Error calling Gemini API: {e}")
                time.sleep(2)

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

