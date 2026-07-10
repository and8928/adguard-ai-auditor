"""
Unit tests for the Settings section: schema validation, runtime config
persistence, the settings service side-effects, and the fetch-step cap.
"""
import asyncio

import pytest
from pydantic import ValidationError


# ---------------------------------------------------------------------------
# Schema: SettingsUpdate validation + to_changes
# ---------------------------------------------------------------------------

class TestSettingsUpdateSchema:
    def test_empty_required_user_rejected(self):
        from src.adguard_auditor.schemas.settings import SettingsUpdate
        with pytest.raises(ValidationError):
            SettingsUpdate(adguard_user="   ")

    def test_empty_url_rejected(self):
        from src.adguard_auditor.schemas.settings import SettingsUpdate
        with pytest.raises(ValidationError):
            SettingsUpdate(adguard_base_url="  ")

    def test_bad_port_rejected(self):
        from src.adguard_auditor.schemas.settings import SettingsUpdate
        with pytest.raises(ValidationError):
            SettingsUpdate(adguard_port="not-a-number")
        with pytest.raises(ValidationError):
            SettingsUpdate(adguard_port="70000")

    def test_empty_secret_skipped_in_changes(self):
        from src.adguard_auditor.schemas.settings import SettingsUpdate
        u = SettingsUpdate(adguard_password="", gemini_api_key="   ")
        assert u.to_changes() == {}

    def test_to_changes_maps_config_keys(self):
        from src.adguard_auditor.schemas.settings import SettingsUpdate
        u = SettingsUpdate(
            adguard_user="admin",
            adguard_port="8080",
            adguard_step_req=250,
            deepseek_api_key="secret",
        )
        changes = u.to_changes()
        assert changes == {
            "ADGUARD_USER": "admin",
            "ADGUARD_PORT": "8080",
            "ADGUARD_STEP_REQ": 250,
            "DEEPSEEK_API_KEY": "secret",
        }

    def test_omitted_fields_absent(self):
        from src.adguard_auditor.schemas.settings import SettingsUpdate
        assert SettingsUpdate().to_changes() == {}


# ---------------------------------------------------------------------------
# config.update_settings — persists to state.env and mutates the singleton
# ---------------------------------------------------------------------------

class TestUpdateSettings:
    def test_writes_and_mutates_known_keys(self, monkeypatch):
        from src.adguard_auditor.core import config

        written = []
        monkeypatch.setattr(config, "set_key", lambda path, k, v: written.append((k, v)))
        # guard originals so monkeypatch restores them after the test
        monkeypatch.setattr(config.settings, "ADGUARD_USER", config.settings.ADGUARD_USER)
        monkeypatch.setattr(config.settings, "ADGUARD_STEP_REQ", config.settings.ADGUARD_STEP_REQ)

        config.update_settings({"ADGUARD_USER": "newuser", "ADGUARD_STEP_REQ": 55})

        assert config.settings.ADGUARD_USER == "newuser"
        assert config.settings.ADGUARD_STEP_REQ == 55
        assert ("ADGUARD_USER", "newuser") in written
        assert ("ADGUARD_STEP_REQ", "55") in written  # persisted as string

    def test_unknown_key_ignored(self, monkeypatch):
        from src.adguard_auditor.core import config
        written = []
        monkeypatch.setattr(config, "set_key", lambda path, k, v: written.append((k, v)))
        config.update_settings({"NOT_A_SETTING": "x"})
        assert written == []


# ---------------------------------------------------------------------------
# endpoints.rebuild — recomputes base URL from current settings
# ---------------------------------------------------------------------------

class TestEndpointsRebuild:
    def test_rebuild_reflects_new_url(self):
        from src.adguard_auditor.core import config
        from src.adguard_auditor.core.endpoints import endpoints

        orig_base = config.settings.ADGUARD_BASE_URL
        orig_port = config.settings.ADGUARD_PORT
        try:
            config.settings.ADGUARD_BASE_URL = "http://example.test"
            config.settings.ADGUARD_PORT = "9999"
            endpoints.rebuild()
            assert endpoints.url == "http://example.test:9999/control"
        finally:
            # Restore settings FIRST, then rebuild, so endpoints.url is clean
            # for other tests (a monkeypatch teardown would run too late).
            config.settings.ADGUARD_BASE_URL = orig_base
            config.settings.ADGUARD_PORT = orig_port
            endpoints.rebuild()


# ---------------------------------------------------------------------------
# settings_service.apply_settings — rebuild / invalidate side-effects
# ---------------------------------------------------------------------------

class TestApplySettings:
    def _patch_env(self, monkeypatch):
        """Stop real state.env writes but keep the singleton mutation."""
        from src.adguard_auditor.core import config
        monkeypatch.setattr(config, "set_key", lambda *a, **k: None)

    def test_url_change_rebuilds_and_invalidates(self, monkeypatch):
        from src.adguard_auditor.schemas.settings import SettingsUpdate
        from src.adguard_auditor.services import settings_service

        self._patch_env(monkeypatch)
        from src.adguard_auditor.core import config
        # guard the mutated attr so monkeypatch restores it after the test
        monkeypatch.setattr(config.settings, "ADGUARD_PORT", config.settings.ADGUARD_PORT)
        calls = {"rebuild": 0, "invalidate": 0}
        monkeypatch.setattr(settings_service.endpoints, "rebuild",
                            lambda: calls.__setitem__("rebuild", calls["rebuild"] + 1))
        monkeypatch.setattr(settings_service.ag_client, "invalidate_session",
                            lambda: calls.__setitem__("invalidate", calls["invalidate"] + 1))

        settings_service.apply_settings(SettingsUpdate(adguard_port="8080"))
        assert calls["rebuild"] == 1
        assert calls["invalidate"] == 1

    def test_step_change_does_not_touch_session(self, monkeypatch):
        from src.adguard_auditor.schemas.settings import SettingsUpdate
        from src.adguard_auditor.services import settings_service

        self._patch_env(monkeypatch)
        from src.adguard_auditor.core import config
        monkeypatch.setattr(config.settings, "ADGUARD_STEP_REQ", config.settings.ADGUARD_STEP_REQ)
        calls = {"rebuild": 0, "invalidate": 0}
        monkeypatch.setattr(settings_service.endpoints, "rebuild",
                            lambda: calls.__setitem__("rebuild", calls["rebuild"] + 1))
        monkeypatch.setattr(settings_service.ag_client, "invalidate_session",
                            lambda: calls.__setitem__("invalidate", calls["invalidate"] + 1))

        settings_service.apply_settings(SettingsUpdate(adguard_step_req=42))
        assert calls["rebuild"] == 0
        assert calls["invalidate"] == 0

    def test_empty_changes_is_noop(self, monkeypatch):
        from src.adguard_auditor.schemas.settings import SettingsUpdate
        from src.adguard_auditor.services import settings_service

        self._patch_env(monkeypatch)
        monkeypatch.setattr(settings_service.endpoints, "rebuild",
                            lambda: pytest.fail("rebuild should not be called"))
        # empty secret -> no changes
        result = settings_service.apply_settings(SettingsUpdate(gemini_api_key=""))
        assert result is not None


# ---------------------------------------------------------------------------
# Fetch-step cap: controller.get_data must not overshoot the requested limit
# ---------------------------------------------------------------------------

class TestFetchStepCap:
    def _run(self, monkeypatch, step_req, limit):
        from src.adguard_auditor.core import config
        from src.adguard_auditor.services import controller
        from src.adguard_auditor.services.controller import ag_client

        monkeypatch.setattr(config.settings, "ADGUARD_STEP_REQ", step_req)
        seen = {}

        def fake_get_querylog(limit=None, next=True):
            seen["limit"] = limit
            return [], False  # nest_stat False -> single iteration

        monkeypatch.setattr(ag_client, "get_querylog", fake_get_querylog)
        ctrl = controller.DataController()
        asyncio.run(ctrl.get_data(limit=limit))
        return seen["limit"]

    def test_small_limit_caps_step(self, monkeypatch):
        assert self._run(monkeypatch, step_req=1000, limit=100) == 100

    def test_zero_limit_uses_full_step(self, monkeypatch):
        assert self._run(monkeypatch, step_req=1000, limit=0) == 1000

    def test_large_limit_uses_step(self, monkeypatch):
        assert self._run(monkeypatch, step_req=100, limit=5000) == 100
