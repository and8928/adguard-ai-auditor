"""
Shared fixtures for all tests.
Environment variables are set BEFORE any project code is imported,
because `settings = Settings()` runs at import time in config.py.
"""
import os
import pytest

# Set test environment variables before any src imports
os.environ.setdefault("ADGUARD_BASE_URL", "http://127.0.0.1")
os.environ.setdefault("ADGUARD_PORT", "3000")
os.environ.setdefault("ADGUARD_USER", "test_user")
os.environ.setdefault("ADGUARD_PASSWORD", "test_pass")
os.environ.setdefault("AGH_SESSION", "test_session_cookie")
os.environ.setdefault("ADGUARD_STEP_REQ", "10")
os.environ.setdefault("GEMINI_MODELS_NAME", '["gemini-test-model"]')
os.environ.setdefault("GEMINI_API_KEY", "test_gemini_key")
os.environ.setdefault("OPENAI_MODEL_NAME", "gpt-test")
os.environ.setdefault("OPENAI_API_KEY", "test_openai_key")
os.environ.setdefault("DEBUG_MOD", "False")


@pytest.fixture
def fastapi_client():
    """Provides a FastAPI TestClient for integration tests."""
    from fastapi.testclient import TestClient
    from src.adguard_auditor.main import app
    with TestClient(app) as client:
        yield client


@pytest.fixture
def sample_querylog_entries():
    """Provides a sample list of raw querylog entries from AdGuard."""
    return [
        {"question": {"name": "analytics.google.com"}, "reason": "NotFilteredNotFound", "filterId": ""},
        {"question": {"name": "tracker.example.com"}, "reason": "NotFilteredNotFound", "filterId": ""},
        {"question": {"name": "cdn.jsdelivr.net"}, "reason": "NotFilteredNotFound", "filterId": ""},
        {"question": {"name": "ads.doubleclick.net"}, "reason": "FilteredBlackList", "filterId": 123},
        {"question": {"name": "telemetry.microsoft.com"}, "reason": "FilteredBlackList", "filterId": 456},
        # Duplicate — should be filtered out
        {"question": {"name": "analytics.google.com"}, "reason": "NotFilteredNotFound", "filterId": ""},
    ]


@pytest.fixture
def sample_filter_rules():
    """Provides a sample list of raw AdGuard filter rules."""
    return [
        "||ads.example.com^",
        "||tracker.example.com^$important",
        "@@||cdn.example.com^",
        "@@||cdn.example.com^$important",
        "||doubleclick.net^",
        "||doubleclick.net^",  # Duplicate
        "! This is a comment",
        "",
        "invalid rule with spaces in domain",
    ]
