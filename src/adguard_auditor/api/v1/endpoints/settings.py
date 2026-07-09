from fastapi import APIRouter, HTTPException
from ....schemas.settings import SettingsRead, SettingsUpdate
from ....services import settings_service
from ....services.adguard_client import ag_client

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SettingsRead)
def get_settings():
    """Current settings. Secrets are returned only as *_set booleans."""
    return settings_service.get_settings()


@router.put("", response_model=SettingsRead)
def update_settings(update: SettingsUpdate):
    """Apply and persist settings. Empty secrets keep the current value."""
    try:
        return settings_service.apply_settings(update)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/test")
def test_connection():
    """Try to log in to AdGuard with the current credentials."""
    return ag_client.test_connection()
