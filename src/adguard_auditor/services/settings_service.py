from ..core.config import settings
from ..core import config as env_config
from ..core.endpoints import endpoints
from ..core.logger import log
from ..schemas.settings import SettingsRead, SettingsUpdate
from .adguard_client import ag_client

# Config keys whose change requires rebuilding the AdGuard base URL.
_URL_KEYS = {"ADGUARD_BASE_URL", "ADGUARD_PORT"}
# Config keys whose change requires forcing a fresh AdGuard login.
_SESSION_KEYS = {"ADGUARD_USER", "ADGUARD_PASSWORD", "ADGUARD_BASE_URL", "ADGUARD_PORT"}


def get_settings() -> SettingsRead:
    """Snapshot of the current settings, with secrets reduced to *_set flags."""
    return SettingsRead(
        adguard_user=settings.ADGUARD_USER,
        adguard_base_url=settings.ADGUARD_BASE_URL,
        adguard_port=settings.ADGUARD_PORT,
        adguard_step_req=settings.ADGUARD_STEP_REQ,
        adguard_password_set=bool(settings.ADGUARD_PASSWORD),
        gemini_api_key_set=bool(settings.GEMINI_API_KEY),
        openai_api_key_set=bool(settings.OPENAI_API_KEY),
        deepseek_api_key_set=bool(settings.DEEPSEEK_API_KEY),
    )


def apply_settings(update: SettingsUpdate) -> SettingsRead:
    """Persist changes, then rebuild endpoints / invalidate session as needed."""
    changes = update.to_changes()

    # Invariant: never persist an empty value into a required credential.
    for key in ("ADGUARD_USER", "ADGUARD_PASSWORD"):
        if key in changes and not str(changes[key]).strip():
            raise ValueError(f"{key} cannot be empty")

    if not changes:
        return get_settings()

    env_config.update_settings(changes)
    log.info(f"[settings] updated keys: {sorted(changes.keys())}")

    if _URL_KEYS & changes.keys():
        endpoints.rebuild()
    if _SESSION_KEYS & changes.keys():
        ag_client.invalidate_session()

    return get_settings()
