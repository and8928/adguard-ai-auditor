import re
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