"""
Unit tests for prompt_rules_service.py - CRUD operations and validation.
Uses a temporary file instead of overwriting the real data/prompt_rules.json.
"""
from unittest.mock import patch

import pytest

from src.adguard_auditor.schemas.prompt_rules import PromptRuleCreate, PromptRuleUpdate
from src.adguard_auditor.services import prompt_rules_service


@pytest.fixture(autouse=True)
def use_temp_rules_file(tmp_path):
    """Redirect the rules file to a temporary location for every test."""
    temp_file = tmp_path / "prompt_rules.json"
    with patch.object(prompt_rules_service, "RULES_FILE", temp_file):
        yield temp_file


class TestCreateRule:
    def test_creates_rule_successfully(self):
        rule = prompt_rules_service.create_rule(
            PromptRuleCreate(name="Test Rule", text="Block all ads from example.com")
        )
        assert rule.name == "Test Rule"
        assert rule.text == "Block all ads from example.com"
        assert rule.is_active is True
        assert rule.id  # Should have a UUID

    def test_created_rule_is_persisted(self):
        rule = prompt_rules_service.create_rule(
            PromptRuleCreate(name="Persisted", text="Some prompt text here")
        )
        fetched = prompt_rules_service.get_rule(rule.id)
        assert fetched is not None
        assert fetched.name == "Persisted"


class TestGetAndListRules:
    def test_get_nonexistent_returns_none(self):
        result = prompt_rules_service.get_rule("nonexistent-id")
        assert result is None

    def test_list_empty(self):
        rules = prompt_rules_service.list_rules()
        assert rules == []

    def test_list_returns_all_rules(self):
        prompt_rules_service.create_rule(PromptRuleCreate(name="Rule A", text="Text A text"))
        prompt_rules_service.create_rule(PromptRuleCreate(name="Rule B", text="Text B text"))
        rules = prompt_rules_service.list_rules()
        assert len(rules) == 2


class TestUpdateRule:
    def test_update_name(self):
        rule = prompt_rules_service.create_rule(
            PromptRuleCreate(name="Original", text="Some text content")
        )
        updated = prompt_rules_service.update_rule(
            rule.id, PromptRuleUpdate(name="Updated Name")
        )
        assert updated.name == "Updated Name"
        assert updated.text == "Some text content"  # Unchanged

    def test_toggle_active(self):
        rule = prompt_rules_service.create_rule(
            PromptRuleCreate(name="Active Rule", text="Some text abc")
        )
        updated = prompt_rules_service.update_rule(
            rule.id, PromptRuleUpdate(is_active=False)
        )
        assert updated.is_active is False

    def test_update_nonexistent_returns_none(self):
        result = prompt_rules_service.update_rule(
            "nonexistent-id", PromptRuleUpdate(name="New")
        )
        assert result is None

    def test_updated_at_is_set(self):
        rule = prompt_rules_service.create_rule(
            PromptRuleCreate(name="Track Time", text="Track time text")
        )
        assert rule.updated_at is None
        updated = prompt_rules_service.update_rule(
            rule.id, PromptRuleUpdate(name="Changed")
        )
        assert updated.updated_at is not None


class TestDeleteRule:
    def test_delete_existing(self):
        rule = prompt_rules_service.create_rule(
            PromptRuleCreate(name="To Delete", text="Delete me pls")
        )
        assert prompt_rules_service.delete_rule(rule.id) is True
        assert prompt_rules_service.get_rule(rule.id) is None

    def test_delete_nonexistent(self):
        assert prompt_rules_service.delete_rule("no-such-id") is False


class TestGetActiveRulesText:
    def test_returns_empty_when_no_rules(self):
        assert prompt_rules_service.get_active_rules_text() == ""

    def test_returns_only_active(self):
        prompt_rules_service.create_rule(
            PromptRuleCreate(name="Active", text="I am active", is_active=True)
        )
        prompt_rules_service.create_rule(
            PromptRuleCreate(name="Inactive", text="I am inactive", is_active=False)
        )
        text = prompt_rules_service.get_active_rules_text()
        assert "I am active" in text
        assert "I am inactive" not in text

    def test_joins_multiple_active_rules(self):
        prompt_rules_service.create_rule(
            PromptRuleCreate(name="Rule 1", text="First rule text")
        )
        prompt_rules_service.create_rule(
            PromptRuleCreate(name="Rule 2", text="Second rule text")
        )
        text = prompt_rules_service.get_active_rules_text()
        assert "First rule text" in text
        assert "Second rule text" in text


class TestPromptRuleValidation:
    def test_reserved_name_rejected(self):
        with pytest.raises(Exception):
            PromptRuleCreate(name="default", text="Some text aaa")

    def test_name_too_short_rejected(self):
        with pytest.raises(Exception):
            PromptRuleCreate(name="", text="Some text bbb")

    def test_text_too_short_rejected(self):
        with pytest.raises(Exception):
            PromptRuleCreate(name="Valid Name", text="ab")
