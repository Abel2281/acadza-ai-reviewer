import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.config import GEMINI_API_KEY, BASE_DIR
from backend.db import init_db
from backend.loader import loader
from backend.routers import results, queue, metrics, actions, audit

# Initialize SQLite database on module import
init_db()

app = FastAPI(
    title="Acadza AI Quality Control API",
    description="Faculty review & automated triage engine API for Acadza JEE/NEET questions",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(results.router)
app.include_router(queue.router)
app.include_router(metrics.router)
app.include_router(actions.router)
app.include_router(audit.router)

@app.get("/api/health")
def health_check():
    loader.reload_results()
    has_key = bool(GEMINI_API_KEY and GEMINI_API_KEY.strip() and GEMINI_API_KEY != "your_gemini_api_key_here")
    return {
        "status": "healthy",
        "ai_enabled": has_key,
        "mode": "live_ai" if has_key else "precomputed",
        "results_count": len(loader.results_raw),
        "reports_count": len(loader.reports_raw),
        "questions_count": len(loader.questions_raw),
        "version": "1.0.0"
    }

# Mount static frontend build if it exists
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        file_path = FRONTEND_DIST / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIST / "index.html")
