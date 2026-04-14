import re
from pydantic import BaseModel, Field
from dataclasses import dataclass
from typing import Optional

@dataclass
class FilterRule:
    """Structure for requests filter"""
    raw: str
    is_exception: bool  # @@
    domain_pattern: str  # ||example.com^
    modifiers: list[str]  # [important, third-party, ...]
    domain: str  # example.com
    is_valid: bool

    @property
    def is_important(self) -> bool:
        return 'important' in self.modifiers

    @property
    def is_third_party(self) -> bool:
        return 'third-party' in self.modifiers

class ConflictWarning(BaseModel):
    domain: str
    pattern: str
    priority_level: str
    conflict_rules: list[str]
    kept_rule: str

class FilterStats(BaseModel):
    total_input_lines: int
    valid_processed: int
    total_clean: int
    duplicates_and_conflicts_removed: int
    equal_power_conflicts: int

class OptimizedRulesSet(BaseModel):
    """Structure for requests filter"""
    clean_rules_objects: dict[str, FilterRule] = Field(default_factory=dict)
    warnings_merged: list[ConflictWarning] = Field(default_factory=list)
    invalid_rules: list[str] = Field(default_factory=list)
    stats: FilterStats