from email.policy import default

from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from ....services import analysis_service
from ....services import controller
from ....schemas.storage import *
from ....schemas.audit import *
from ....core.logger import log
import asyncio
from src.gemini import init as gemini

router = APIRouter()
templates = Jinja2Templates(directory="src/adguard_auditor/frontend/templates")


@router.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    pass
    # Главная страница с кнопкой "Начать анализ"
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/get-row-request-log")
def get_row_request_log(limit: int = 100) -> RowData:
    """
    Return row logs form AdGuard server
    :param limit: if 0 - No limit, get data for all of time
    """
    ctrl = controller.DataController()
    return asyncio.run(ctrl.get_data(limit=limit))


@router.get("/get-response-log")
def get_response_log(limit: int = 100) -> dict[str, list]:
    """
    Return clin logs form AdGuard server
    :param limit: if 0 - No limit, get data for all of time
    """
    ctrl = controller.DataController()
    asyncio.run(ctrl.get_data(limit=limit))
    return ctrl.clean_data()


@router.post("/ai-analis-data")
def filter_data(data: str, model_services: ModelServices = Query(
    default=ModelServices.GEMINI,
    description="Выберите модель для анализа данных",
    examples={
        "gemini": {"value": "gemini", "summary": "Google Gemini"},
        "chatgpt": {"value": "chatgpt", "summary": "OpenAI ChatGPT"},
        "qwen": {"value": "qwen", "summary": "Alibaba Qwen"},
    }
)

                ) -> AnalysisResponse:
    """
    Return clin logs form AdGuard server
    :param data: data for analysis witch llm
    :param model_services: model name
    """
    result = gemini.generate(data)
    # print(json.dumps(result, indent=2, ensure_ascii=False))
    return result


@router.post("/auto-analis")
def auto_analis(limit: int = 0, model_services: ModelServices = Query(
    default=ModelServices.GEMINI,
    description="Выберите модель для анализа данных",
    examples={
        "gemini": {"value": "gemini", "summary": "Google Gemini"},
        "chatgpt": {"value": "chatgpt", "summary": "OpenAI ChatGPT"},
        "qwen": {"value": "qwen", "summary": "Alibaba Qwen"},
    }
)

                ) -> AnalysisResponse:
    """
    Return clin logs form AdGuard server
    :param data: data for analysis witch llm
    :param model_services: model name
    """

    ctrl = controller.DataController()
    asyncio.run(ctrl.get_data(limit=limit))
    if ctrl.clean_data():
        result = gemini.generate(str(ctrl.clean_data()))
    else:
        {"Error":"No data"}
    # print(json.dumps(result, indent=2, ensure_ascii=False))
    return result

@router.post("/to_block")
def to_block(data: BlockRequest):
    """
    Принимает четкую структуру данных для блокировки.
    Раньше было data: str, теперь валидированный объект.
    """
    filters = get_actual_filter()
    print(f"data = {data}")
    for el in data.domains:
        print(el.domain)
        if el.domain in filters['full_domain_list']:
            # for i in
            print("Have!")
        else:
            print("No!")

    return {
        "status": "success",
        "blocked_count": False,
        "message": f"Domains queued for blocking with reason: Flase"
    }

@router.get("/get_actual_filter")
def get_actual_filter() -> dict:
    ctrl = controller.DataController()
    log.debug(f"[audit][get_actual_filter] -> start")
    return ctrl.get_actual_filter()
