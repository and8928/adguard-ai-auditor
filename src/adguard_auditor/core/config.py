# init config (read .env)
from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from pathlib import Path
from dotenv import set_key

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
ENV_PATH = os.path.join(BASE_DIR, ".env")
STATE_PATH = os.path.join(BASE_DIR, "data", "state.env")

class Settings(BaseSettings):
    PROJECT_NAME: str = "AdGuard AI Auditor"
    ADGUARD_BASE_URL: str = "http://host.docker.internal"
    ADGUARD_USER: str
    ADGUARD_PASSWORD: str
    ADGUARD_PORT: str = "80"
    ADGUARD_STEP_REQ: int = 100

    AGH_SESSION: str = ""

    GEMINI_MODELS_NAME: list
    GEMINI_API_KEY: str

    VERTEX_AI_MODELS_NAME: list = []
    VERTEX_AI_API_KEY: str = ""

    OPENAI_MODEL_NAME: str
    OPENAI_API_KEY: str

    DEEPSEEK_MODELS_NAME: list
    DEEPSEEK_API_KEY: str
    DEEPSEEK_REASONING_EFFORT: str
    DEEPSEEK_THINKING_ENABLED: bool

    DEBUG_MOD: bool = False

    model_config = SettingsConfigDict(
        env_file=(ENV_PATH, STATE_PATH),
        env_file_encoding='utf-8',
        extra='ignore'
    )

settings = Settings()

# Keys that may be edited at runtime via the Settings section, with the
# type used to coerce the value before it is stored on the settings singleton.
RUNTIME_SETTINGS: dict[str, type] = {
    "ADGUARD_USER": str,
    "ADGUARD_PASSWORD": str,
    "ADGUARD_BASE_URL": str,
    "ADGUARD_PORT": str,
    "ADGUARD_STEP_REQ": int,
    "GEMINI_API_KEY": str,
    "OPENAI_API_KEY": str,
    "DEEPSEEK_API_KEY": str,
}


def _apply_runtime_value(key: str, value):
    """Persist a single value to state.env and update the settings singleton."""
    set_key(STATE_PATH, key, str(value))
    if hasattr(settings, key):
        setattr(settings, key, value)


def update_settings(changes: dict):
    """
    Persist a batch of runtime settings to state.env and update the in-memory
    singleton. Only keys listed in RUNTIME_SETTINGS are accepted; each value is
    coerced to the declared type.
    """
    for key, value in changes.items():
        if key not in RUNTIME_SETTINGS:
            continue
        coerced = RUNTIME_SETTINGS[key](value)
        _apply_runtime_value(key, coerced)


def update_agh_session(agh_session: str):
    """
    update agh_session in state.env.
    """
    _apply_runtime_value("AGH_SESSION", agh_session)


def update_step_req(value: int):
    """
    update step_req in state.env.
    """
    _apply_runtime_value("ADGUARD_STEP_REQ", int(value))