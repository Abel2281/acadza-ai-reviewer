import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.config import (
    DATA_DIR, GEMINI_MODEL, QUESTIONS_FILE, REPORTS_FILE, TAXONOMY_FILE,
    RESULTS_FILE,
)
from scripts.triage.engine import TriageEngine
from scripts.triage.gemini_client import GeminiClient

NORMAL_PROGRESS_FILE = DATA_DIR / "triage_progress.json"
SMOKE_RESULTS_FILE = DATA_DIR / "gemini_smoke_test.json"
SMOKE_PROGRESS_FILE = DATA_DIR / "gemini_smoke_test_progress.json"


class SmokeTestRunError(RuntimeError):
    def __init__(self, api_calls_made: int, stage: str, diagnostic: str):
        super().__init__(diagnostic)
        self.api_calls_made = api_calls_made
        self.stage = stage
        self.diagnostic = diagnostic


def _safe_smoke_diagnostic(exc: Exception, client) -> str:
    client_diagnostic = getattr(client, "last_error", None)
    if client_diagnostic:
        return str(client_diagnostic)
    if isinstance(exc, json.JSONDecodeError):
        return f"Invalid JSON at line {exc.lineno}, column {exc.colno}."
    if isinstance(exc, FileNotFoundError):
        return f"Required local file is missing: {Path(exc.filename).name if exc.filename else 'unknown file'}."
    if isinstance(exc, PermissionError):
        return "Access to a required local file was denied."
    message = str(exc)
    safe_engine_messages = (
        "GEMINI_API_KEY is required; use --dry-run for mocked analysis",
    )
    if message.startswith(("API call limit reached", "Batch ", "Not every selected report", "Report coverage", "Result schema")):
        return message
    if message in safe_engine_messages:
        return "GEMINI_API_KEY is missing or is still set to the placeholder value."
    return f"Unexpected {type(exc).__name__}; no sensitive exception details were printed."


def _print_smoke_request_diagnostics(metrics: dict) -> None:
    print(
        "Smoke request size: "
        f"{metrics['prompt_characters']} prompt characters; "
        f"{metrics['request_body_bytes']} serialized UTF-8 bytes; "
        f"{metrics['question_groups']} question groups; {metrics['reports']} reports."
    )
    print(
        "Included source text: "
        f"{metrics['question_text_characters']} question characters; "
        f"{metrics['solution_text_characters']} solution characters."
    )


def prepare_progress(progress_path: Path, resume: bool, fresh_run: bool) -> None:
    if resume and fresh_run:
        raise ValueError("Choose either --resume or --fresh-run")
    if resume:
        if not progress_path.exists():
            raise FileNotFoundError(f"No saved progress exists at {progress_path}")
        return
    if progress_path.exists() and not fresh_run:
        raise FileExistsError(
            f"Saved triage progress exists at {progress_path}; use --resume to continue "
            "or --fresh-run to explicitly discard it."
        )
    if progress_path.exists():
        progress_path.unlink()


def run_smoke_test(client=None, dry_run: bool = False):
    """Analyze only the first batch and write exclusively to smoke-test artifacts."""
    stage = "configure isolated smoke-test client"
    engine = None
    try:
        if client is None:
            client = GeminiClient()
        if isinstance(client, GeminiClient):
            # Keep the one-POST ceiling and smoke-specific timeout even when a
            # configured GeminiClient is injected by a caller.
            client.configure_smoke_test()
        stage = "load local question, report, and taxonomy datasets"
        with open(QUESTIONS_FILE, encoding="utf-8") as f:
            questions = json.load(f)
        with open(REPORTS_FILE, encoding="utf-8") as f:
            reports = json.load(f)
        with open(TAXONOMY_FILE, encoding="utf-8") as f:
            taxonomy = json.load(f)

        stage = "initialize engine and load runtime prompts"
        engine = TriageEngine(
            questions, reports, taxonomy,
            client=client,
            dry_run=dry_run,
            progress_path=SMOKE_PROGRESS_FILE, max_batches=1, max_api_calls=1,
            diagnostics_callback=_print_smoke_request_diagnostics,
        )
        stage = "validate first batch and perform smoke triage"
        results = engine.process_all_reports()
        stage = "write isolated smoke-test output"
        temp_file = SMOKE_RESULTS_FILE.with_suffix(".tmp")
        temp_file.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
        temp_file.replace(SMOKE_RESULTS_FILE)
    except Exception as exc:
        stage = getattr(engine, "current_stage", stage)
        actual_posts = getattr(client, "http_posts_made", None) if client is not None else None
        if actual_posts is None:
            actual_posts = engine.api_calls_made if engine is not None else 0
        raise SmokeTestRunError(actual_posts, stage, _safe_smoke_diagnostic(exc, client)) from exc
    actual_posts = getattr(client, "http_posts_made", None)
    if actual_posts is None:
        actual_posts = engine.api_calls_made
    return results, actual_posts


def main():
    parser = argparse.ArgumentParser(description="Run sequential, resumable Acadza Gemini triage")
    parser.add_argument("--dry-run", action="store_true", help="Use deterministic mock responses; no API calls")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--resume", action="store_true", help="Resume saved partial progress")
    mode.add_argument("--fresh-run", action="store_true", help="Explicitly discard saved progress and start over")
    mode.add_argument("--smoke-test", action="store_true", help="Analyze one batch with a strict one-request limit and isolated files")
    args = parser.parse_args()
    if args.smoke_test:
        try:
            results, api_calls_made = run_smoke_test(dry_run=args.dry_run)
        except SmokeTestRunError as exc:
            print("Smoke test failed; no validated output was written by this run.")
            print(f"Failure stage: {exc.stage}")
            print(f"Diagnostic: {exc.diagnostic}")
            print(f"Gemini API requests: {exc.api_calls_made}")
            print(f"Model: {GEMINI_MODEL}")
            print(f"Output: {SMOKE_RESULTS_FILE}")
            raise SystemExit(1) from exc
        print(f"Smoke test processed {len(results)} reports with {api_calls_made} Gemini API request(s).")
        print(f"Model: {GEMINI_MODEL}")
        print(f"Output: {SMOKE_RESULTS_FILE}")
        return
    progress_path = NORMAL_PROGRESS_FILE
    try:
        prepare_progress(progress_path, args.resume, args.fresh_run)
    except (FileExistsError, FileNotFoundError, ValueError) as exc:
        parser.error(str(exc))
    with open(QUESTIONS_FILE, encoding="utf-8") as f:
        questions = json.load(f)
    with open(REPORTS_FILE, encoding="utf-8") as f:
        reports = json.load(f)
    with open(TAXONOMY_FILE, encoding="utf-8") as f:
        taxonomy = json.load(f)
    engine = TriageEngine(questions, reports, taxonomy, dry_run=args.dry_run, progress_path=progress_path)
    results = engine.process_all_reports()
    if len(results) != len(reports):
        raise RuntimeError("Incomplete triage; results.json was not written")
    temp_file = RESULTS_FILE.with_suffix(".tmp")
    temp_file.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    temp_file.replace(RESULTS_FILE)
    source = "mock/reference" if args.dry_run else "Gemini"
    print(f"Wrote {len(results)} validated {source} results to {RESULTS_FILE}")


if __name__ == "__main__":
    main()
