from typing import Literal

from pydantic import BaseModel, Field


class RowData(BaseModel):
    row_data: list = Field(default_factory=list)


class DomainBase(BaseModel):
    domain: str
    reason: str


class DomainDecision(DomainBase):
    confidence: Literal["LOW", "MEDIUM", "HIGH"]


class AnalysisResponse(BaseModel):
    domains_to_block: list[DomainDecision]
    domains_to_unblock: list[DomainDecision]
    domains_to_test: list[DomainBase]
    analysis_summary: str


class BlockRequest(BaseModel):
    domains: list[DomainDecision]


class DomainNamesRequest(BaseModel):
    """Lightweight request carrying only domain names (e.g. for manual delete)."""
    domains: list[str]
