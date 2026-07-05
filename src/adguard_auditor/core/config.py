# Управление конфигурацией (чтение .env)
from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "AdGuard AI Auditor"
    ADGUARD_BASE_URL: str
    ADGUARD_USER: str
    ADGUARD_PASSWORD: str
    ADGUARD_PORT: str
    ADGUARD_STEP_REQ: int

    AGH_SESSION: str

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
        env_file=os.path.join(BASE_DIR, ".env"),
        env_file_encoding='utf-8'
    )


settings = Settings()
