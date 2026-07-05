"""
Unit tests for adguard_client.py - session management and HTTP interactions.
Uses the `responses` library to mock all HTTP requests to AdGuard Home.
"""
from time import time
from unittest.mock import patch

import responses

from src.adguard_auditor.core.endpoints import endpoints
from src.adguard_auditor.services.adguard_client import AdGuardController

PROFILE_URL = endpoints.get_url(endpoints.PROFILE)
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

    @responses.activate
    def test_returns_true_on_200(self):
        """HTTP 200 from profile endpoint means session is valid."""
        responses.add(responses.GET, PROFILE_URL, status=200)
        ctrl = self._make_controller(session_last_check=0)
        assert ctrl.check_session() is True

    @responses.activate
    def test_returns_false_on_401_no_auto_create(self):
        """HTTP 401 with auto_create=False should return False, not a string."""
        responses.add(responses.GET, PROFILE_URL, status=401)
        ctrl = self._make_controller(session_last_check=0)
        result = ctrl.check_session(auto_create=False)
        assert result is False
        assert isinstance(result, bool)

    @responses.activate
    def test_returns_false_on_401_with_auto_create_exhausted(self):
        """HTTP 401 with auto_create=True but _get_new_session is a no-op should exhaust retries and return False."""
        # Two requests: first attempt + one retry
        responses.add(responses.GET, PROFILE_URL, status=401)
        responses.add(responses.GET, PROFILE_URL, status=401)
        ctrl = self._make_controller(session_last_check=0)
        result = ctrl.check_session(attempts=1)
        assert result is False

    @responses.activate
    def test_returns_false_on_unexpected_status_code(self):
        """HTTP 500 should return False."""
        responses.add(responses.GET, PROFILE_URL, status=500)
        ctrl = self._make_controller(session_last_check=0)
        result = ctrl.check_session()
        assert result is False

    @responses.activate
    def test_calls_get_new_session_on_401(self):
        """On 401 with auto_create=True, _get_new_session should be called."""
        responses.add(responses.GET, PROFILE_URL, status=401)
        responses.add(responses.GET, PROFILE_URL, status=401)
        ctrl = self._make_controller(session_last_check=0)
        with patch.object(ctrl, "_get_new_session") as mock_new:
            ctrl.check_session(attempts=1)
            mock_new.assert_called()

    @responses.activate
    def test_updates_session_last_check_on_success(self):
        """On success, session_last_check should be updated to ~now."""
        responses.add(responses.GET, PROFILE_URL, status=200)
        ctrl = self._make_controller(session_last_check=0)
        before = int(time())
        ctrl.check_session()
        assert ctrl.session_last_check >= before


class TestGetQuerylog:
    @responses.activate
    def test_returns_bad_session_on_failed_check(self):
        """If check_session fails, get_querylog should return 'Bad session'."""
        responses.add(responses.GET, PROFILE_URL, status=401)
        ctrl = AdGuardController()
        ctrl.session_last_check = 0
        result = ctrl.get_querylog(next=False)
        assert result == "Bad session"

    @responses.activate
    def test_returns_data_on_success(self):
        """On success, should return (data_list, has_more_bool)."""
        responses.add(responses.GET, PROFILE_URL, status=200)
        querylog_response = {"data": [{"question": {"name": "test.com"}}], "oldest": "2025-01-01T00:00:00Z"}
        responses.add(
            responses.GET,
            QUERYLOG_URL_PREFIX,
            json=querylog_response,
            status=200,
            match_querystring=False,
        )
        ctrl = AdGuardController()
        ctrl.session_last_check = 0
        data, has_more = ctrl.get_querylog(next=False)
        assert len(data) == 1
        assert has_more is True

    @responses.activate
    def test_returns_false_on_querylog_error(self):
        """On non-200 from querylog endpoint, should return (False, False)."""
        responses.add(responses.GET, PROFILE_URL, status=200)
        responses.add(
            responses.GET,
            QUERYLOG_URL_PREFIX,
            status=500,
            match_querystring=False,
        )
        ctrl = AdGuardController()
        ctrl.session_last_check = 0
        data, has_more = ctrl.get_querylog(next=False)
        assert data is False
        assert has_more is False
        assert ctrl.bad_requests is True


class TestGetActualFilter:
    @responses.activate
    def test_returns_user_rules_on_success(self):
        responses.add(responses.GET, PROFILE_URL, status=200)
        responses.add(
            responses.GET,
            FILTERING_URL,
            json={"user_rules": ["||ads.com^", "@@||cdn.com^"]},
            status=200,
        )
        ctrl = AdGuardController()
        ctrl.session_last_check = 0
        result = ctrl.get_actual_filter()
        assert result == ["||ads.com^", "@@||cdn.com^"]

    @responses.activate
    def test_returns_bad_session_on_auth_fail(self):
        responses.add(responses.GET, PROFILE_URL, status=401)
        ctrl = AdGuardController()
        ctrl.session_last_check = 0
        result = ctrl.get_actual_filter()
        assert result == "Bad session"


class TestSetActualFilter:
    @responses.activate
    def test_returns_true_on_success(self):
        responses.add(responses.GET, PROFILE_URL, status=200)
        responses.add(responses.POST, SET_FILTERING_URL, status=200)
        ctrl = AdGuardController()
        ctrl.session_last_check = 0
        assert ctrl.set_actual_filter(["||test.com^"]) is True

    @responses.activate
    def test_returns_false_on_auth_fail(self):
        responses.add(responses.GET, PROFILE_URL, status=401)
        ctrl = AdGuardController()
        ctrl.session_last_check = 0
        assert ctrl.set_actual_filter(["||test.com^"]) is False

    @responses.activate
    def test_returns_false_on_server_error(self):
        responses.add(responses.GET, PROFILE_URL, status=200)
        responses.add(responses.POST, SET_FILTERING_URL, status=500, body="Internal Server Error")
        ctrl = AdGuardController()
        ctrl.session_last_check = 0
        assert ctrl.set_actual_filter(["||test.com^"]) is False
