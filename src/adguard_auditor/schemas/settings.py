from pydantic import BaseModel, Field, field_validator
from typing import Optional


# Secret fields: never revealed by GET, and an empty value means "keep current".
_SECRET_KEYS = {"adguard_password", "gemini_api_key", "openai_api_key", "deepseek_api_key"}

# Maps SettingsUpdate field -> config/state.env key.
_FIELD_TO_CONFIG = {
    "adguard_user": "ADGUARD_USER",
    "adguard_password": "ADGUARD_PASSWORD",
    "adguard_base_url": "ADGUARD_BASE_URL",
    "adguard_port": "ADGUARD_PORT",
    "adguard_step_req": "ADGUARD_STEP_REQ",
    "gemini_api_key": "GEMINI_API_KEY",
    "openai_api_key": "OPENAI_API_KEY",
    "deepseek_api_key": "DEEPSEEK_API_KEY",
}


class SettingsRead(BaseModel):
    """Current settings for the UI. Secrets are exposed only as *_set booleans."""
    adguard_user: str
    adguard_base_url: str
    adguard_port: str
    adguard_step_req: int
    adguard_password_set: bool
    gemini_api_key_set: bool
    openai_api_key_set: bool
    deepseek_api_key_set: bool


class SettingsUpdate(BaseModel):
    """Partial update. Omitted fields (and empty secrets) are left unchanged."""
    adguard_user: Optional[str] = None
    adguard_password: Optional[str] = None
    adguard_base_url: Optional[str] = None
    adguard_port: Optional[str] = None
    adguard_step_req: Optional[int] = Field(default=None, ge=1)
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    deepseek_api_key: Optional[str] = None

    @field_validator("adguard_user", "adguard_base_url")
    @classmethod
    def required_not_blank(cls, v: Optional[str]) -> Optional[str]:
        # These are revealed by GET, so an explicit empty value is an intent to
        # clear a required field -> reject.
        if v is not None and not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip() if v is not None else v

    @field_validator("adguard_port")
    @classmethod
    def port_must_be_numeric(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not v.isdigit() or not (0 < int(v) <= 65535):
            raise ValueError("Port must be a number between 1 and 65535")
        return v

    def to_changes(self) -> dict:
        """Return {CONFIG_KEY: value} for fields that should actually be applied.

        Omitted fields are skipped; empty secrets are skipped (keep current).
        """
        changes: dict = {}
        data = self.model_dump(exclude_unset=True)
        for field, value in data.items():
            if value is None:
                continue
            if field in _SECRET_KEYS and isinstance(value, str) and not value.strip():
                continue  # empty secret -> keep current
            changes[_FIELD_TO_CONFIG[field]] = value
        return changes
