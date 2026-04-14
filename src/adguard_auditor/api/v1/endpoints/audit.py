from fastapi import APIRouter, Request, Query, HTTPException
from ....schemas.adguard_models import OptimizedRulesSet
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from ....services import analysis_service
from src.gemini import init as gemini
from ....services import controller
from ....schemas.storage import *
from ....schemas.audit import *
from ....core.logger import log
import asyncio

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
def auto_analis(limit: int = 0, user_prompt: str = Query(
    default="",
    description="Suggestions, for example, wbsg8v.xyz is not a dangerous domain, I use it"
), model_services: ModelServices = Query(
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
        result = gemini.generate(str(ctrl.clean_data()), user_prompt=user_prompt)
    else:
        {"Error": "No data"}
    # print(json.dumps(result, indent=2, ensure_ascii=False))
    return result


@router.post("/to_block")
def to_block(data: BlockRequest):
    """Blocked selected domains"""
    ctrl = controller.DataController()

    optimized_rules = ctrl.get_actual_filter()

    domains_list = [item.domain for item in data.domains]

    final_raw_rules, stats = analysis_service.apply_blocks_to_rules(optimized_rules, domains_list)

    success = ctrl.set_actual_filter(final_raw_rules)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to save rules in AdGuard")

    return {
        "status": "success",
        "action": "block",
        "stats": stats,
        "message": f"Successfully processed {len(domains_list)} domains."
    }


@router.post("/to_unblock")
def to_unblock(data: BlockRequest):
    """UnBlocked selected domains"""
    ctrl = controller.DataController()
    optimized_rules = ctrl.get_actual_filter()
    domains_list = [item.domain for item in data.domains]

    final_raw_rules, stats = analysis_service.apply_unblocks_to_rules(optimized_rules, domains_list)

    success = ctrl.set_actual_filter(final_raw_rules)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to save rules in AdGuard")

    return {
        "status": "success",
        "action": "unblock",
        "stats": stats,
        "message": f"Successfully processed {len(domains_list)} domains."
    }


@router.get("/get_actual_filter")
def get_actual_filter() -> OptimizedRulesSet:
    ctrl = controller.DataController()
    log.debug(f"[audit][get_actual_filter] -> start")
    return ctrl.get_actual_filter()
