from tabnanny import check
from src.adguard_auditor.core.logger import log
from src.adguard_auditor.core.config import settings
import requests
import json


class AdGuardController:
    def __init__(self):
        self.url: str = f"{settings.ADGUARD_URL}:{settings.ADGUARD_PORT}"
        self.port: int = settings.ADGUARD_PORT
        self.base: str = settings.ADGUARD_REQ_BASE
        self.cookies = settings.AGH_SESSION
        self.oldest: str = ""

    def check_session(self, attempts: int = 1, auto_create: bool = True):
        result = requests.get(url=self.url,
                              cookies={'agh_session': self.cookies})
        sc = result.status_code
        if sc == 200:
            log.info(f"[check_session][status] -> OK")
            return True
        elif sc == 401:
            if auto_create:
                self._get_new_session()
            else:
                attempts = 0
            log.info(f"[check_session][status] -> Create new" if attempts > 0 else f"[check_session][status] -> Fail")
            return self.check_session(
                attempts=attempts - 1) if attempts > 0 else f"Error get new session | auto_create is {auto_create}"

    def _get_new_session(self):
        pass

    def get_data(self, limit=settings.ADGUARD_STEP_REQ, next: str = True):
        if not self.check_session():
            return 'Bad session'
        if next and self.oldest !="":
            oldest = f"&older_than={self.oldest}"
        else:
            oldest = ''
        result = requests.get(url=f"{self.url}{settings.ADGUARD_REQ_BASE}{limit}{oldest}",
                              cookies={'agh_session': settings.AGH_SESSION})
        log.debug(f"[get_data][status_code] -> {result.status_code}")
        log.debug(f"[get_data][text] -> {result.text}")
        if result.status_code == 200:
            result_dict = json.loads(result.text)
            self.oldest = result_dict['oldest']
            nest_stat = False if self.oldest == "" else True
            return result_dict['data'], nest_stat
        else:
            log.error(f"[get_data][status_code] -> {result.status_code}")
            return False, False

    def get_actual_filter(self):
        """Getting actual user filter"""
        pass

ag_client = AdGuardController()
