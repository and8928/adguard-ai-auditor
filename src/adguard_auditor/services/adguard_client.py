import json
from time import time

import httpx

from src.adguard_auditor.core.config import settings
from src.adguard_auditor.core import config as env_config
from src.adguard_auditor.core.endpoints import endpoints
from src.adguard_auditor.core.logger import log

# httpx defaults to a 5s timeout; querylog fetches with a large step can take longer
REQUEST_TIMEOUT = 30.0


class AdGuardController:
    def __init__(self):
        self.agh_session = settings.AGH_SESSION
        self.oldest: str = ""
        self.session_last_check: int = 0
        self.bad_requests: bool = False

    def check_session(self, auto_create: bool = True) -> bool:
        if self.session_last_check + 1800 > int(time()) and not self.bad_requests:
            return True
        url = endpoints.get_url(endpoints.PROFILE)
        result = httpx.get(url=url, cookies={'agh_session': self.agh_session}, timeout=REQUEST_TIMEOUT)
        sc = result.status_code
        if sc == 200:
            log.info(f"[check_session][status] -> OK")
            self.session_last_check = int(time())
            return True
        elif sc == 401:
            log.info(f"[check_session][status] -> 401")
            self.session_last_check = -1
            if auto_create:
                log.info(f"[check_session][status] -> Create new")
                self._get_new_session()
                return self.check_session(auto_create=False)
            log.error(f"[check_session] -> Error get new session | auto_create is {auto_create}")
            return False
        else:
            log.error(f"[check_session] -> Unexpected status code: {sc}")
            return False

    def _get_new_session(self) -> str:
        """Sreate new session to adguard"""
        url = endpoints.get_url(endpoints.LOGIN)
        payload = {"name": f"{settings.ADGUARD_USER}", "password": f"{settings.ADGUARD_PASSWORD}"}
        result = httpx.post(url=url, json=payload, timeout=REQUEST_TIMEOUT)
        log.debug(f"[adguard_client][get_new_session] -> status: {result.status_code}")
        log.debug(f"result.__dict__ = {result.__dict__}")

        if result.status_code == 200:
            log.info(f"[adguard_client][get_new_session] -> Successful login")
            self.agh_session = result.cookies.get("agh_session")
            log.info(f"[adguard_client][get_new_session] -> update .env")
            env_config.update_agh_session(self.agh_session)
            return "Successful login"
        else:
            error_message = f"Error login!: {result.reason_phrase} | {result.status_code}"
            log.error(error_message)
            return error_message

    def get_querylog(self, limit: int = None, next: bool = True):
        if not limit:
            limit = settings.ADGUARD_STEP_REQ
        if not self.check_session():
            return 'Bad session'
        if next and self.oldest != "":
            oldest = f"&older_than={self.oldest.replace('+', '%2B')}"
        else:
            oldest = ''
        url = endpoints.get_url(endpoints.QUERYLOG, limit=limit, oldest=oldest)
        result = httpx.get(url=url, cookies={'agh_session': self.agh_session}, timeout=REQUEST_TIMEOUT)
        log.debug(f"[get_querylog][status_code] -> {result.status_code}")
        log.debug(f"[get_querylog][text] -> {result.text}")
        if result.status_code == 200:
            result_dict = json.loads(result.text)
            self.oldest = result_dict['oldest']
            nest_stat = False if self.oldest == "" else True
            return result_dict['data'], nest_stat
        else:
            log.error(f"[get_querylog][status_code] -> {result.status_code}")
            self.bad_requests = True
            return False, False

    def get_actual_filter(self):
        """Getting actual user filter"""
        if not self.check_session():
            return 'Bad session'
        url = endpoints.get_url(endpoints.FILTERING)
        log.debug(f"[get_actual_filter][url] -> {url}")
        result = httpx.get(url=url, cookies={'agh_session': self.agh_session}, timeout=REQUEST_TIMEOUT)
        log.debug(f"[adguard_client][get_actual_filter][status_code] -> {result.status_code}")
        log.debug(f"[adguard_client][get_actual_filter][text] -> {result.text}")
        if result.status_code == 200:
            result_dict = json.loads(result.text)
            return result_dict['user_rules']
        else:
            log.error(f"[get_actual_filter][status_code] -> {result.status_code}")
            self.bad_requests = True
            return False

    def set_actual_filter(self, raw_rules: list[str]) -> bool:
        """Send an update list of rules"""
        if not self.check_session():
            return False

        url = endpoints.get_url(endpoints.SET_FILTERING)
        # AdGuard API {"rules": ["rule1", "rule2"]}
        payload = {"rules": raw_rules}

        result = httpx.post(url=url, json=payload, cookies={'agh_session': self.agh_session}, timeout=REQUEST_TIMEOUT)
        log.debug(f"[adguard_client][set_actual_filter] -> status: {result.status_code}")

        if result.status_code == 200:
            return True
        else:
            log.error(f"Error setting filter: {result.text}")
            return False

    def login(self):
        """Login to adguard"""
        return self.check_session()

    def invalidate_session(self):
        """Force a re-login on the next request (after credentials/URL change)."""
        self.agh_session = settings.AGH_SESSION
        self.session_last_check = -1
        self.bad_requests = False

    def test_connection(self) -> dict:
        """Check AGH_SESSION. Used by POST /settings/test."""
        result = self.check_session(auto_create = False)
        ok = result == True
        return {"ok": ok, "message": result}

    def test_login(self) -> dict:
        """Try to log in with the current credentials. Used by POST /settings/test."""
        result = self._get_new_session()
        ok = result == "Successful login"
        return {"ok": ok, "message": result}



ag_client = AdGuardController()
