from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime


class PromptRuleCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=50, pattern=r'^[a-zA-Z0-9_-]+$')
    text: str = Field(..., min_length=3, max_length=2000)
    description: Optional[str] = Field(default=None, max_length=200)

    @field_validator('title')
    @classmethod
    def title_must_be_unique_slug(cls, v: str) -> str:
        if v.lower() in ['default', 'none', 'null']:
            raise ValueError('Title cannot be a reserved keyword')
        return v


class PromptRule(PromptRuleCreate):
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None


class PromptRuleList(BaseModel):
    rules: list[PromptRule]
    total: int