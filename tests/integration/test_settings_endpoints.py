"""
Integration tests for the /settings endpoints.
state.env writes are patched out so tests never touch real files.
"""
import pytest


@pytest.fixture
def no_env_writes(monkeypatch):
    """Prevent real state.env writes while keeping singleton mutation."""
    from src.adguard_auditor.core import config
    monkeypatch.setattr(config, "set_key", lambda *a, **k: None)


class TestGetSettings:
    def test_returns_masked_secrets(self, fastapi_client):
        response = fastapi_client.get("/api/v1/settings")
        assert response.status_code == 200
        data = response.json()
        # Non-secret fields are exposed…
        assert data["adguard_user"] == "test_user"
        assert data["adguard_base_url"]
        # …secrets are only *_set booleans, never plaintext values.
        assert "adguard_password" not in data
        assert "gemini_api_key" not in data
        assert data["adguard_password_set"] is True
        assert data["gemini_api_key_set"] is True


class TestPutSettings:
    def test_update_step_req(self, fastapi_client, no_env_writes, monkeypatch):
        from src.adguard_auditor.core import config
        monkeypatch.setattr(config.settings, "ADGUARD_STEP_REQ", config.settings.ADGUARD_STEP_REQ)

        response = fastapi_client.put("/api/v1/settings", json={"adguard_step_req": 321})
        assert response.status_code == 200
        assert response.json()["adguard_step_req"] == 321

    def test_empty_user_rejected(self, fastapi_client, no_env_writes):
        response = fastapi_client.put("/api/v1/settings", json={"adguard_user": "   "})
        assert response.status_code == 422  # schema-level validation

    def test_credential_change_invalidates_session(self, fastapi_client, no_env_writes, monkeypatch):
        from src.adguard_auditor.services.adguard_client import ag_client
        from src.adguard_auditor.core import config
        monkeypatch.setattr(config.settings, "ADGUARD_PORT", config.settings.ADGUARD_PORT)
        called = {"n": 0}
        monkeypatch.setattr(ag_client, "invalidate_session",
                            lambda: called.__setitem__("n", called["n"] + 1))
        monkeypatch.setattr("src.adguard_auditor.core.endpoints.endpoints.rebuild", lambda: None)

        response = fastapi_client.put("/api/v1/settings", json={"adguard_port": "8080"})
        assert response.status_code == 200
        assert called["n"] == 1


class TestTestLogin:
    def test_success(self, fastapi_client, monkeypatch):
        from src.adguard_auditor.services.adguard_client import ag_client
        monkeypatch.setattr(ag_client, "_get_new_session", lambda: "Successful login")
        response = fastapi_client.post("/api/v1/settings/test_login")
        assert response.status_code == 200
        assert response.json() == {"ok": True, "message": "Successful login"}

    def test_failure(self, fastapi_client, monkeypatch):
        from src.adguard_auditor.services.adguard_client import ag_client
        monkeypatch.setattr(ag_client, "_get_new_session", lambda: "Error login!: Unauthorized | 401")
        response = fastapi_client.post("/api/v1/settings/test_login")
        assert response.status_code == 200
        assert response.json()["ok"] is False

class TestTestConnection:
    def test_success(self, fastapi_client, monkeypatch):
        from src.adguard_auditor.services.adguard_client import ag_client
        monkeypatch.setattr(ag_client, "check_session", lambda **kw: True)
        response = fastapi_client.post("/api/v1/settings/test_connection")
        assert response.status_code == 200
        assert response.json() == {"ok": True, "message": True}

    def test_failure(self, fastapi_client, monkeypatch):
        from src.adguard_auditor.services.adguard_client import ag_client
        monkeypatch.setattr(ag_client, "check_session", lambda **kw: False)
        response = fastapi_client.post("/api/v1/settings/test_connection")
        assert response.status_code == 200
        assert response.json()["ok"] is False
