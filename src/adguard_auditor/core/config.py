# Управление конфигурацией (чтение .env)
from pydantic_settings import BaseSettings
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

    OPENAI_MODEL_NAME: str
    OPENAI_API_KEY: str

    DEBUG_MOD: bool = False

    class Config:
        env_file = os.path.join(BASE_DIR, ".env")
        print(f"init .env file in: {env_file}")
        env_file_encoding = 'utf-8'


settings = Settings()
