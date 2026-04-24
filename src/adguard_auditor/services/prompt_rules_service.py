import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional
from ..core.logger import log
from ..schemas.prompt_rules import PromptRule, PromptRuleCreate

RULES_FILE = Path(__file__).parent.parent.parent.parent / "data" / "prompt_rules.json"


def _ensure_file():
    """Create file"""
    RULES_FILE.parent.mkdir(exist_ok=True)
    if not RULES_FILE.exists():
        RULES_FILE.write_text(json.dumps({"rules": {}}, indent=2, ensure_ascii=False))


def _load_rules() -> dict:
    _ensure_file()
    try:
        return json.loads(RULES_FILE.read_text(encoding='utf-8'))
    except json.JSONDecodeError:
        log.warning("Corrupted prompt_rules.json, resetting...")
        _ensure_file()
        return {"rules": {}}


def _save_rules(data: dict):
    _ensure_file()
    RULES_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def create_rule(rule: PromptRuleCreate) -> PromptRule:
    data = _load_rules()
    if rule.title in data["rules"]:
        raise ValueError(f"Rule '{rule.title}' already exists")

    new_rule = PromptRule(**rule.model_dump())
    data["rules"][rule.title] = new_rule.model_dump(mode='json')
    _save_rules(data)
    log.info(f"Created prompt rule: {rule.title}")
    return new_rule


def get_rule(title: str) -> Optional[PromptRule]:
    data = _load_rules()
    rule_data = data["rules"].get(title)
    return PromptRule(**rule_data) if rule_data else None


def list_rules() -> list[PromptRule]:
    data = _load_rules()
    return [PromptRule(**r) for r in data["rules"].values()]


def delete_rule(title: str) -> bool:
    data = _load_rules()
    if title not in data["rules"]:
        return False
    del data["rules"][title]
    _save_rules(data)
    log.info(f"Deleted prompt rule: {title}")
    return True


def resolve_prompt_input(user_input: str) -> str:
    """
    if user_input — this name pomts then return promt text.
    else return raw text
    """
    if not user_input.strip():
        return ""

    saved = get_rule(user_input.strip())
    if saved:
        log.debug(f"Resolved prompt rule '{user_input}' -> {len(saved.text)} chars")
        return saved.text

    return user_input