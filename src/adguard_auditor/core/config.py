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

def update_agh_session(agh_session: str):
    """
    update agh_session in state.env.
    """
    set_key(STATE_PATH, "AGH_SESSION", agh_session)
    if hasattr(settings, "AGH_SESSION"):
        setattr(settings, "AGH_SESSION", agh_session)

def update_step_req(value: int):
    """
    update step_req in state.env.
    """
    set_key(STATE_PATH, "ADGUARD_STEP_REQ", str(value))
    if hasattr(settings, "ADGUARD_STEP_REQ"):
        setattr(settings, "ADGUARD_STEP_REQ", value)