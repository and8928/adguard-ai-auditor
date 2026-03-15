from tabnanny import check
from src.adguard_auditor.core.logger import log
from src.adguard_auditor.core.config import settings
from src.adguard_auditor.core.endpoints import endpoints
from time import time
import requests
import json


class AdGuardController:
    def __init__(self):
        self.cookies = settings.AGH_SESSION
        self.oldest: str = ""
        self.session_last_check: int = 0
        self.bad_requests: bool = False

    def check_session(self, attempts: int = 1, auto_create: bool = True) -> bool:
        if self.session_last_check + 1800 > int(time()) and not self.bad_requests:
            return True
        url = endpoints.get_url(endpoints.PROFILE)
        result = requests.get(url=url,
                              cookies={'agh_session': self.cookies})
        sc = result.status_code
        if sc == 200:
            log.info(f"[check_session][status] -> OK")
            self.session_last_check = int(time())
            return True
        elif sc == 401:
            self.session_last_check = -1
            if auto_create:
                self._get_new_session()
            else:
                attempts = 0
            log.info(f"[check_session][status] -> Create new" if attempts > 0 else f"[check_session][status] -> Fail")
            return self.check_session(
                attempts=attempts - 1) if attempts > 0 else f"Error get new session | auto_create is {auto_create}"

    def _get_new_session(self):
        pass

    def get_querylog(self, limit=settings.ADGUARD_STEP_REQ, next: str = True):
        if not self.check_session():
            return 'Bad session'
        if next and self.oldest != "":
            oldest = f"&older_than={self.oldest}"
        else:
            oldest = ''
        url = endpoints.get_url(endpoints.QUERYLOG, limit=limit, oldest=oldest)
        result = requests.get(url=url, cookies={'agh_session': settings.AGH_SESSION})
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
        print(f"url = {url}")
        result = requests.get(url=url, cookies={'agh_session': settings.AGH_SESSION})
        log.debug(f"[adguard_client][get_actual_filter][status_code] -> {result.status_code}")
        log.debug(f"[adguard_client][get_actual_filter][text] -> {result.text}")
        if result.status_code == 200:
            result_dict = json.loads(result.text)
            print(f"result_dict = {result_dict['user_rules']}")
            return result_dict['user_rules']
        else:
            log.error(f"[get_actual_filter][status_code] -> {result.status_code}")
            self.bad_requests = True
            return False, False


ag_client = AdGuardController()
