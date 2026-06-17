from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from src.adguard_auditor import __version__
from src.adguard_auditor.api.v1.endpoints import audit, prompt_rules
from src.adguard_auditor.core.config import settings

BASE_DIR = Path(__file__).resolve().parent
app = FastAPI(title=settings.PROJECT_NAME, version=__version__)

app.include_router(audit.router, prefix="/api/v1")
app.include_router(prompt_rules.router, prefix="/api/v1")


@app.get("/", include_in_schema=False)
async def root_redirect():
    """Redirect from root to the dashboard page."""
    return RedirectResponse(url="/api/v1/")


static_path = BASE_DIR / "frontend" / "static"
if not static_path.exists():
    static_path.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
