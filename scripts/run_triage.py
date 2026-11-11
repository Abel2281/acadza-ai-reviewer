import sys
import json
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.config import QUESTIONS_FILE, REPORTS_FILE, TAXONOMY_FILE, RESULTS_FILE
from scripts.triage.engine import TriageEngine

def main():
    print("=" * 60)
    print("Acadza AI Triage Engine — Processing all 44 student reports")
    print("=" * 60)

    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        questions = json.load(f)
    with open(REPORTS_FILE, "r", encoding="utf-8") as f:
        reports = json.load(f)
    with open(TAXONOMY_FILE, "r", encoding="utf-8") as f:
        taxonomy = json.load(f)

    print(f"Loaded {len(questions)} questions, {len(reports)} reports, and taxonomy.")

    engine = TriageEngine(questions, reports, taxonomy)
    results = engine.process_all_reports()

    print(f"Successfully processed {len(results)} reports.")

    # Validation checks
    assert len(results) == len(reports), f"Expected {len(reports)} results, got {len(results)}"
    
    route_counts = {}
    verdict_counts = {}
    for r in results:
        route = r["route"]
        route_counts[route] = route_counts.get(route, 0) + 1
        v = r["verdict"]
        verdict_counts[v] = verdict_counts.get(v, 0) + 1

    print("\nRoute breakdown:")
    for k, v in route_counts.items():
        print(f"  {k:15}: {v}")

    print("\nVerdict breakdown:")
    for k, v in verdict_counts.items():
        print(f"  {k:15}: {v}")

    # Write atomically
    temp_file = RESULTS_FILE.with_suffix(".tmp")
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    temp_file.replace(RESULTS_FILE)

    print(f"\nWritten verified results to: {RESULTS_FILE}")
    print("=" * 60)

if __name__ == "__main__":
    main()

