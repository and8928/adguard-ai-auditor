from fastapi import APIRouter, HTTPException
from ....schemas.prompt_rules import PromptRuleCreate, PromptRuleUpdate, PromptRule, PromptRuleList
from ....services import prompt_rules_service

router = APIRouter(prefix="/prompt-rules", tags=["prompt-rules"])


@router.post("", response_model=PromptRule, status_code=201)
def create_prompt_rule(rule: PromptRuleCreate):
    """Create a prompt rule"""
    try:
        return prompt_rules_service.create_rule(rule)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=PromptRuleList)
def list_prompt_rules():
    """Get all prompt rules"""
    rules = prompt_rules_service.list_rules()
    return PromptRuleList(rules=rules, total=len(rules))


@router.get("/{rule_id}", response_model=PromptRule)
def get_prompt_rule(rule_id: str):
    """Get a prompt rule by id"""
    rule = prompt_rules_service.get_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail=f"Rule '{rule_id}' not found")
    return rule


@router.patch("/{rule_id}", response_model=PromptRule)
def update_prompt_rule(rule_id: str, rule_update: PromptRuleUpdate):
    """Update a prompt rule (e.g., toggle is_active)"""
    rule = prompt_rules_service.update_rule(rule_id, rule_update)
    if not rule:
        raise HTTPException(status_code=404, detail=f"Rule '{rule_id}' not found")
    return rule


@router.delete("/{rule_id}")
def delete_prompt_rule(rule_id: str):
    """Delete by id"""
    if not prompt_rules_service.delete_rule(rule_id):
        raise HTTPException(status_code=404, detail=f"Rule '{rule_id}' not found")
    return {"status": "deleted", "id": rule_id}


@router.get("/{rule_id}/test")
def test_prompt_rule(rule_id: str):
    """Test get"""
    rule = prompt_rules_service.get_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail=f"Rule '{rule_id}' not found")

    return {"id": rule.id, "name": rule.name, "injected_prompt_block": rule.text}