"""
Unit tests for adguard_client.py - session management and HTTP interactions.
Uses the `respx` library to mock all HTTP requests (httpx) to AdGuard Home.
"""
from time import time
from unittest.mock import patch

import httpx
import respx

from src.adguard_auditor.core.endpoints import endpoints
from src.adguard_auditor.services.adguard_client import AdGuardController

PROFILE_URL = endpoints.get_url(endpoints.PROFILE)
LOGIN_URL = endpoints.get_url(endpoints.LOGIN)
QUERYLOG_URL_PREFIX = f"{endpoints.url}/querylog"
FILTERING_URL = endpoints.get_url(endpoints.FILTERING)
SET_FILTERING_URL = endpoints.get_url(endpoints.SET_FILTERING)


class TestCheckSession:
    def _make_controller(self, **overrides):
        ctrl = AdGuardController()
        for k, v in overrides.items():
            setattr(ctrl, k, v)
        return ctrl

    def test_returns_true_from_cache(self):
        """If session was checked recently, return True without HTTP call."""
        ctrl = self._make_controller(
            session_last_check=int(time()),  # Fresh check
            bad_requests=False,
        )
        # No HTTP mock needed - should not make a request
        assert ctrl.check_session() is True

    @respx.mock
    def test_returns_true_on_200(self):
        """HTTP 200 from profile endpoint means session is valid."""
        respx.get(PROFILE_URL).mock(return_value=httpx.Response(200))
        ctrl = self._make_controller(session_last_check=0)
        assert ctrl.check_session() is True

    @respx.mock
    def test_returns_false_on_401_no_auto_create(self):
        """HTTP 401 with auto_create=False should return False, not a string."""
        respx.get(PROFILE_URL).mock(return_value=httpx.Response(401))
        ctrl = self._make_controller(session_last_check=0)
        result = ctrl.check_session(auto_create=False)
        assert result is False
        assert isinstance(result, bool)

    @respx.mock
    def test_returns_false_on_401_with_auto_create_exhausted(self):
        """HTTP 401 with auto_create=True but login also fails should exhaust retries and return False."""
        # profile stays 401 (first attempt + retry) and the login attempt fails too
        respx.get(PROFILE_URL).mock(return_value=httpx.Response(401))
        respx.post(LOGIN_URL).mock(return_value=httpx.Response(401))
        ctrl = self._make_controller(session_last_check=0)
        result = ctrl.check_session()
        assert result is False

    @respx.mock
    def test_returns_false_on_unexpected_status_code(self):
        """HTTP 500 should return False."""
        respx.get(PROFILE_URL).mock(return_value=httpx.Response(500))
        ctrl = self._make_controller(session_last_check=0)
        result = ctrl.check_session()
        assert result is False

    @respx.mock
    def test_calls_get_new_session_on_401(self):
        """On 401 with auto_create=True, _get_new_session should be called."""
        respx.get(PROFILE_URL).mock(return_value=httpx.Response(401))
        ctrl = self._make_controller(session_last_check=0)
        with patch.object(ctrl, "_get_new_session") as mock_new:
            ctrl.check_session()
            mock_new.assert_called()

    @respx.mock
    def test_updates_session_last_check_on_success(self):
        """On success, session_last_check should be updated to ~now."""
        respx.get(PROFILE_URL).mock(return_value=httpx.Response(200))
        ctrl = self._make_controller(session_last_check=0)
        before = int(time())
        ctrl.check_session()
        assert ctrl.session_last_check >= before


class TestGetQuerylog:
    @respx.mock
    def test_returns_bad_session_on_failed_check(self):
        """If check_session fails, get_querylog should return 'Bad session'."""
        respx.get(PROFILE_URL).mock(return_value=httpx.Response(401))
        respx.post(LOGIN_URL).mock(return_value=httpx.Response(401))
        ctrl = AdGuardController()
        ctrl.session_last_check = 0
        result = ctrl.get_querylog(next=False)
        assert result == "Bad session"

    @respx.mock
    def test_returns_data_on_success(self):
        """On success, should return (data_list, has_more_bool)."""
        respx.get(PROFILE_URL).mock(return_value=httpx.Response(200))
        querylog_response = {"data": [{"question": {"name": "test.com"}}], "oldest": "2025-01-01T00:00:00Z"}
        respx.get(url__startswith=QUERYLOG_URL_PREFIX).mock(
            return_value=httpx.Response(200, json=querylog_response)
        )
        ctrl = AdGuardController()
        ctrl.session_last_check = 0
        data, has_more = ctrl.get_querylog(next=False)
        assert len(data) == 1
        assert has_more is True

    @respx.mock
    def test_returns_false_on_querylog_error(self):
        """On non-200 from querylog endpoint, should return (False, False)."""
        respx.get(PROFILE_URL).mock(return_value=httpx.Response(200))
        respx.get(url__startswith=QUERYLOG_URL_PREFIX).mock(
            return_value=httpx.Response(500)
        )
        ctrl = AdGuardController()
        ctrl.session_last_check = 0
        data, has_more = ctrl.get_querylog(next=False)
        assert data is False
        assert has_more is False
        assert ctrl.bad_requests is True


class TestGetActualFilter:
    @respx.mock
    def test_returns_user_rules_on_success(self):
        respx.get(PROFILE_URL).mock(return_value=httpx.Response(200))
        respx.get(FILTERING_URL).mock(
            return_value=httpx.Response(200, json={"user_rules": ["||ads.com^", "@@||cdn.com^"]})
        )
        ctrl = AdGuardController()
        ctrl.session_last_check = 0
        result = ctrl.get_actual_filter()
        assert result == ["||ads.com^", "@@||cdn.com^"]

    @respx.mock
    def test_returns_bad_session_on_auth_fail(self):
        respx.get(PROFILE_URL).mock(return_value=httpx.Response(401))
        respx.post(LOGIN_URL).mock(return_value=httpx.Response(401))
        ctrl = AdGuardController()
        ctrl.session_last_check = 0
        result = ctrl.get_actual_filter()
        assert result == "Bad session"


class TestSetActualFilter:
    @respx.mock
    def test_returns_true_on_success(self):
        respx.get(PROFILE_URL).mock(return_value=httpx.Response(200))
        respx.post(SET_FILTERING_URL).mock(return_value=httpx.Response(200))
        ctrl = AdGuardController()
        ctrl.session_last_check = 0
        assert ctrl.set_actual_filter(["||test.com^"]) is True

    @respx.mock
    def test_returns_false_on_auth_fail(self):
        respx.get(PROFILE_URL).mock(return_value=httpx.Response(401))
        respx.post(LOGIN_URL).mock(return_value=httpx.Response(401))
        ctrl = AdGuardController()
        ctrl.session_last_check = 0
        assert ctrl.set_actual_filter(["||test.com^"]) is False

    @respx.mock
    def test_returns_false_on_server_error(self):
        respx.get(PROFILE_URL).mock(return_value=httpx.Response(200))
        respx.post(SET_FILTERING_URL).mock(
            return_value=httpx.Response(500, text="Internal Server Error")
        )
        ctrl = AdGuardController()
        ctrl.session_last_check = 0
        assert ctrl.set_actual_filter(["||test.com^"]) is False
