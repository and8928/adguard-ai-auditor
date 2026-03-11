from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from src.adguard_auditor.api.v1.endpoints import audit
from src.adguard_auditor.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(audit.router, prefix="/api/v1")
app.mount("/static", StaticFiles(directory="src/adguard_auditor/frontend/static"), name="static")