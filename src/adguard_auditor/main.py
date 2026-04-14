import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from src.adguard_auditor.api.v1.endpoints import audit
from src.adguard_auditor.core.config import settings

BASE_DIR = Path(__file__).resolve().parent
app = FastAPI(title=settings.PROJECT_NAME)
app.include_router(audit.router, prefix="/api/v1")

static_path = BASE_DIR / "frontend" / "static"
if not static_path.exists():
    static_path.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(static_path)), name="static")