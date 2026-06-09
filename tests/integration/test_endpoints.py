"""
Integration tests for FastAPI API endpoints.
All external dependencies (AdGuard client, Gemini) are mocked.
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient




class TestIndexPage:
    def test_returns_html(self, fastapi_client):
        response = fastapi_client.get("/api/v1/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]




class TestGetActualFilter:
    def test_returns_optimized_rules(self, fastapi_client):
        mock_rules = ["||ads.com^", "@@||cdn.com^"]
        with patch(
            "src.adguard_auditor.services.adguard_client.ag_client.get_actual_filter",
            return_value=mock_rules,
        ), patch(
            "src.adguard_auditor.services.adguard_client.ag_client.check_session",
            return_value=True,
        ):
            response = fastapi_client.get("/api/v1/get_actual_filter")
            assert response.status_code == 200
            data = response.json()
            assert "stats" in data
            assert "clean_rules_objects" in data




class TestToBlock:
    def test_block_domains_success(self, fastapi_client):
        mock_rules = ["||existing.com^"]
        with patch(
            "src.adguard_auditor.services.adguard_client.ag_client.get_actual_filter",
            return_value=mock_rules,
        ), patch(
            "src.adguard_auditor.services.adguard_client.ag_client.check_session",
            return_value=True,
        ), patch(
            "src.adguard_auditor.services.adguard_client.ag_client.set_actual_filter",
            return_value=True,
        ):
            response = fastapi_client.post("/api/v1/to_block", json={
                "domains": [
                    {"domain": "tracker.com", "reason": "Tracking", "confidence": "HIGH"}
                ]
            })
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["action"] == "block"

    def test_block_returns_422_on_invalid_payload(self, fastapi_client):
        response = fastapi_client.post("/api/v1/to_block", json={
            "domains": [{"invalid_field": "value"}]
        })
        assert response.status_code == 422




class TestToUnblock:
    def test_unblock_domains_success(self, fastapi_client):
        mock_rules = ["||blocked.com^"]
        with patch(
            "src.adguard_auditor.services.adguard_client.ag_client.get_actual_filter",
            return_value=mock_rules,
        ), patch(
            "src.adguard_auditor.services.adguard_client.ag_client.check_session",
            return_value=True,
        ), patch(
            "src.adguard_auditor.services.adguard_client.ag_client.set_actual_filter",
            return_value=True,
        ):
            response = fastapi_client.post("/api/v1/to_unblock", json={
                "domains": [
                    {"domain": "blocked.com", "reason": "False positive", "confidence": "HIGH"}
                ]
            })
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["action"] == "unblock"




class TestPromptRulesEndpoints:
    def test_list_empty(self, fastapi_client):
        with patch(
            "src.adguard_auditor.services.prompt_rules_service.list_rules",
            return_value=[],
        ):
            response = fastapi_client.get("/api/v1/prompt-rules")
            assert response.status_code == 200
            data = response.json()
            assert data["rules"] == []
            assert data["total"] == 0

    def test_create_and_get(self, fastapi_client):
        from src.adguard_auditor.schemas.prompt_rules import PromptRule
        mock_rule = PromptRule(name="Test Rule", text="Test text content")
        with patch(
            "src.adguard_auditor.services.prompt_rules_service.create_rule",
            return_value=mock_rule,
        ):
            response = fastapi_client.post("/api/v1/prompt-rules", json={
                "name": "Test Rule",
                "text": "Test text content",
            })
            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "Test Rule"

    def test_delete_nonexistent_returns_404(self, fastapi_client):
        with patch(
            "src.adguard_auditor.services.prompt_rules_service.delete_rule",
            return_value=False,
        ):
            response = fastapi_client.delete("/api/v1/prompt-rules/nonexistent-id")
            assert response.status_code == 404
