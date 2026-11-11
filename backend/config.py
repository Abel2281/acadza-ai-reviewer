import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
BACKEND_DIR = BASE_DIR / "backend"

# Load backend/.env if present
load_dotenv(BACKEND_DIR / ".env")

QUESTIONS_FILE = DATA_DIR / "questions.json"
REPORTS_FILE = DATA_DIR / "reports.json"
TAXONOMY_FILE = DATA_DIR / "taxonomy.json"
RESULTS_FILE = DATA_DIR / "results.json"
DB_FILE = BACKEND_DIR / "audit.db"

# Model identifier (default to gemini-2.0-flash or as specified)
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Triage configuration
BATCH_SIZE = 5
MAX_API_CALLS = 10

