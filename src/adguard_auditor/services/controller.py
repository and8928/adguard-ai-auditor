from src.adguard_auditor.services.adguard_client import ag_client
from src.adguard_auditor.services import analysis_service
from src.adguard_auditor.schemas.storage import RowData
from src.adguard_auditor.core.config import settings
from src.adguard_auditor.core.logger import log

class DataController:
    def __init__(self):
        self.data = RowData()

    async def get_data(self, limit: int = 0):
        """

        :param limit: if 0 - No limit, get data for all of time

        """
        i = 0
        step = settings.ADGUARD_STEP_REQ
        while True:
            i += 1
            row_data, nest_stat = ag_client.get_querylog(next = False if i == 1 else True)
            log.debug(f"[get_data][row_data] -> {row_data}")
            log.debug(f"[get_data][nest_stat] -> {nest_stat}")
            if row_data == False:
                log.error(f"[get_data] -> !!! ERROR ag_client.get_data return False !!!")
                return False
            self.data.row_data.extend(row_data)
            if not nest_stat or (limit != 0 and limit <= step*i):
                break
        return self.data

    def clean_data(self) -> dict:
        result = analysis_service.clean_and_prepare_logs(self.data.row_data)
        return result

    def get_actual_filter(self):
        log.debug(f"[controller][get_actual_filter] -> start")
        row_data = ag_client.get_actual_filter()
        return analysis_service.optimize_filtering_rules(row_data)
