import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional
import uuid
from ..core.logger import log
from ..schemas.prompt_rules import PromptRule, PromptRuleCreate, PromptRuleUpdate

RULES_FILE = Path(__file__).parent.parent.parent.parent / "data" / "prompt_rules.json"


def _ensure_file():
    """Create file"""
    RULES_FILE.parent.mkdir(exist_ok=True)
    if not RULES_FILE.exists():
        RULES_FILE.write_text(json.dumps({"rules": {}}, indent=2, ensure_ascii=False))


def _load_rules() -> dict:
    _ensure_file()
    try:
        data = json.loads(RULES_FILE.read_text(encoding='utf-8'))
        # Migration from title-based to id-based if needed
        migrated = False
        rules = data.get("rules", {})
        new_rules = {}
        for k, v in rules.items():
            if "id" not in v:
                v["id"] = str(uuid.uuid4())
                if "title" in v:
                    v["name"] = v.pop("title")
                v["is_active"] = v.get("is_active", True)
                migrated = True
            new_rules[v["id"]] = v
            
        if migrated:
            data["rules"] = new_rules
            _save_rules(data)
            
        return data
    except json.JSONDecodeError:
        log.warning("Corrupted prompt_rules.json, resetting...")
        _ensure_file()
        return {"rules": {}}


def _save_rules(data: dict):
    _ensure_file()
    RULES_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def create_rule(rule: PromptRuleCreate) -> PromptRule:
    data = _load_rules()
    
    new_rule = PromptRule(**rule.model_dump())
    data["rules"][new_rule.id] = new_rule.model_dump(mode='json')
    _save_rules(data)
    log.info(f"Created prompt rule: {new_rule.name} (ID: {new_rule.id})")
    return new_rule


def get_rule(rule_id: str) -> Optional[PromptRule]:
    data = _load_rules()
    rule_data = data["rules"].get(rule_id)
    return PromptRule(**rule_data) if rule_data else None


def list_rules() -> list[PromptRule]:
    data = _load_rules()
    return [PromptRule(**r) for r in data["rules"].values()]


def update_rule(rule_id: str, rule_update: PromptRuleUpdate) -> Optional[PromptRule]:
    data = _load_rules()
    if rule_id not in data["rules"]:
        return None
        
    rule_data = data["rules"][rule_id]
    rule = PromptRule(**rule_data)
    
    update_data = rule_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(rule, key, value)
        
    rule.updated_at = datetime.now()
    data["rules"][rule_id] = rule.model_dump(mode='json')
    _save_rules(data)
    log.info(f"Updated prompt rule: {rule.name} (ID: {rule.id})")
    return rule


def delete_rule(rule_id: str) -> bool:
    data = _load_rules()
    if rule_id not in data["rules"]:
        return False
    del data["rules"][rule_id]
    _save_rules(data)
    log.info(f"Deleted prompt rule: {rule_id}")
    return True


def get_active_rules_text() -> str:
    """
    Returns a combined string of all active rules' text.
    """
    data = _load_rules()
    active_texts = []
    for r in data["rules"].values():
        if r.get("is_active", True):
            active_texts.append(r.get("text", ""))
            
    if not active_texts:
        return ""
        
    return "\n\n".join(active_texts)