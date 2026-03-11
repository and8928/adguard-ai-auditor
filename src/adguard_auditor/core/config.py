# Управление конфигурацией (чтение .env)
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "AdGuard AI Auditor"
    ADGUARD_URL: str
    ADGUARD_USER: str
    ADGUARD_PASSWORD: str
    ADGUARD_PORT: str
    ADGUARD_STEP_REQ: int

    AGH_SESSION: str
    ADGUARD_REQ_BASE: str

    GEMINI_MODELS_NAME: list
    GEMINI_API_KEY: str

    OPENAI_MODEL_NAME: str
    OPENAI_API_KEY: str

    class Config:
        env_file = ".env"


settings = Settings()
