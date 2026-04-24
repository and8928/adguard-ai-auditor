from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from ....schemas.prompt_rules import PromptRuleCreate, PromptRule, PromptRuleList
from ....services import prompt_rules_service

router = APIRouter(prefix="/prompt-rules", tags=["prompt-rules"])


@router.post("", response_model=PromptRule, status_code=201)
def create_prompt_rule(rule: PromptRuleCreate):
    """Save promt"""
    try:
        return prompt_rules_service.create_rule(rule)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=PromptRuleList)
def list_prompt_rules():
    """Get all promts"""
    rules = prompt_rules_service.list_rules()
    return PromptRuleList(rules=rules, total=len(rules))


@router.get("/{title}", response_model=PromptRule)
def get_prompt_rule(title: str):
    """get promt by title"""
    rule = prompt_rules_service.get_rule(title)
    if not rule:
        raise HTTPException(status_code=404, detail=f"Rule '{title}' not found")
    return rule


@router.delete("/{title}")
def delete_prompt_rule(title: str):
    """Delete by title"""
    if not prompt_rules_service.delete_rule(title):
        raise HTTPException(status_code=404, detail=f"Rule '{title}' not found")
    return {"status": "deleted", "title": title}


@router.get("/{title}/test")
def test_prompt_rule(title: str):
    """Test get"""
    rule = prompt_rules_service.get_rule(title)
    if not rule:
        raise HTTPException(status_code=404, detail=f"Rule '{title}' not found")

    return {"title": rule.title, "injected_prompt_block": rule.text}