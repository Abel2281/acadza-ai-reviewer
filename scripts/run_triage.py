import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.config import QUESTIONS_FILE, REPORTS_FILE, TAXONOMY_FILE, RESULTS_FILE
from scripts.triage.engine import TriageEngine


def main():
    parser = argparse.ArgumentParser(description="Run sequential, resumable Acadza Gemini triage")
    parser.add_argument("--dry-run", action="store_true", help="Use deterministic mock responses; no API calls")
    parser.add_argument("--resume", action="store_true", help="Resume saved partial progress")
    args = parser.parse_args()
    progress_path = ROOT_DIR / "data" / "triage_progress.json"
    if not args.resume and progress_path.exists():
        progress_path.unlink()
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
