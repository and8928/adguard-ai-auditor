from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
import uuid


class PromptRuleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    text: str = Field(..., min_length=3, max_length=2000)
    description: Optional[str] = Field(default=None, max_length=200)
    is_active: bool = Field(default=True)

    @field_validator('name')
    @classmethod
    def name_must_not_be_reserved(cls, v: str) -> str:
        if v.lower() in ['default', 'none', 'null']:
            raise ValueError('Name cannot be a reserved keyword')
        return v


class PromptRuleUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    text: Optional[str] = Field(default=None, min_length=3, max_length=2000)
    description: Optional[str] = Field(default=None, max_length=200)
    is_active: Optional[bool] = None


class PromptRule(PromptRuleCreate):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None


class PromptRuleList(BaseModel):
    rules: list[PromptRule]
    total: int