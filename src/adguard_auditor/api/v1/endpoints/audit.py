import asyncio
import json
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, Request, Query, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from src.gemini import init as gemini
from src.vertex_ai import init as vertex_ai
from src.deepseek import init as deepseek
from .... import __version__
from ....core.config import settings
from ....core.logger import log
from ....schemas.adguard_models import OptimizedRulesSet
from ....schemas.audit import *
from ....schemas.storage import *
from ....services import analysis_service, controller, prompt_rules_service
from ....services.adguard_client import ag_client
from ....services.cache import audit_cache


class AuditAction(str, Enum):
    FULL = "full"
    FETCH = "fetch"
    ANALYZE = "analyze"


router = APIRouter()
templates = Jinja2Templates(directory="src/adguard_auditor/frontend/templates")

_executor = ThreadPoolExecutor(max_workers=2)


@router.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    return templates.TemplateResponse(request, "index.html", {"version": __version__})


@router.get("/get-raw-request-log")
def get_raw_request_log(limit: int = 100) -> RowData:
    """
    Return raw logs from the AdGuard server
    :param limit: if 0 - No limit, get data for all of time
    """
    ctrl = controller.DataController()
    return asyncio.run(ctrl.get_data(limit=limit))


@router.get("/get-response-log")
def get_response_log(limit: int = 100) -> dict[str, list]:
    """
    Return cleaned logs from the AdGuard server
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
        "deepseek": {"value": "deepseek", "summary": "DeepSeek"},
    }
)) -> AnalysisResponse:
    """
    Run LLM analysis on the supplied data.
    :param data: data to analyze with the LLM
    :param model_services: model name
    """
    if model_services == ModelServices.VERTEX_AI:
        result = vertex_ai.generate(data)
    elif model_services == ModelServices.DEEPSEEK:
        result = deepseek.generate(data)
    else:
        result = gemini.generate(data)

    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
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
        "deepseek": {"value": "deepseek", "summary": "DeepSeek"},
    }
)) -> AnalysisResponse:
    """
    Fetch logs from AdGuard, clean them and run LLM analysis.
    :param limit: if 0 - No limit, get data for all of time
    :param user_prompt: additional user instructions for the LLM
    :param model_services: model name
    """

    ctrl = controller.DataController()
    asyncio.run(ctrl.get_data(limit=limit))
    if not ctrl.clean_data():
        raise HTTPException(status_code=400, detail="No data")

    active_rules_text = prompt_rules_service.get_active_rules_text()
    final_user_prompt = f"{active_rules_text}\n\n{user_prompt}".strip()

    if model_services == ModelServices.VERTEX_AI:
        result = vertex_ai.generate(str(ctrl.clean_data()), user_prompt=final_user_prompt)
    elif model_services == ModelServices.DEEPSEEK:
        result = deepseek.generate(str(ctrl.clean_data()), user_prompt=final_user_prompt)
    else:
        result = gemini.generate(str(ctrl.clean_data()), user_prompt=final_user_prompt)

    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    return result


@router.get("/audit/stream")
async def audit_stream(
        limit: int = Query(default=0, description="Log limit (0 = all)"),
        user_prompt: str = Query(default="", description="Additional user instructions for AI"),
        model_services: ModelServices = Query(default=ModelServices.GEMINI, description="AI model to use"),
        action: AuditAction = Query(default=AuditAction.FULL, description="full | fetch | analyze"),
):
    """SSE endpoint for real-time audit progress streaming.

    action=full   – fetch + clean + cache + LLM (original behaviour)
    action=fetch  – fetch + clean + cache, then stop
    action=analyze – read from cache, run LLM only
    """

    async def event_generator():
        loop = asyncio.get_event_loop()
        cleaned = None

        # ── Steps 1-2 (fetch & clean) - skipped when action=analyze ──
        if action in (AuditAction.FULL, AuditAction.FETCH):
            # Step 1: Fetch logs from AdGuard
            try:
                ctrl = controller.DataController()
                step_size = settings.ADGUARD_STEP_REQ
                total_count = 0
                iteration = 0

                while True:
                    iteration += 1
                    row_data, has_next = await loop.run_in_executor(
                        _executor,
                        lambda: ag_client.get_querylog(
                            limit=step_size,
                            next=(iteration > 1),
                        )
                    )

                    if row_data is False:
                        yield _sse({"status": "error", "step": "fetch",
                                    "message": "Failed to fetch data from AdGuard. Check session."})
                        return

                    ctrl.data.row_data.extend(row_data)
                    total_count += len(row_data) if isinstance(row_data, list) else 0
                    yield _sse({"status": "fetching", "count": total_count})

                    if not has_next or (limit != 0 and limit <= step_size * iteration):
                        break

                yield _sse({"status": "fetch_done", "count": total_count})

            except Exception as e:
                log.error(f"[audit/stream] Fetch error: {e}")
                yield _sse({"status": "error", "step": "fetch", "message": str(e)})
                return

            # Step 2: Clean and group data
            try:
                cleaned = await loop.run_in_executor(_executor, ctrl.clean_data)
                allowed_count = len(cleaned.get("Allowed", []))
                blocked_count = len(cleaned.get("Blocked", []))
                yield _sse({"status": "cleaning", "allowed": allowed_count, "blocked": blocked_count})

                if not cleaned or (allowed_count == 0 and blocked_count == 0):
                    yield _sse({"status": "error", "step": "clean", "message": "No data to analyze after cleaning."})
                    return

                # Save to cache
                audit_cache.store(cleaned, allowed_count, blocked_count)

                yield _sse({
                    "status": "clean_done",
                    "allowed": allowed_count,
                    "blocked": blocked_count,
                    "model": model_services.value,
                    "cache": audit_cache.status(),
                })

            except Exception as e:
                log.error(f"[audit/stream] Clean error: {e}")
                yield _sse({"status": "error", "step": "clean", "message": str(e)})
                return

            # If fetch-only mode, stop here
            if action == AuditAction.FETCH:
                yield _sse({"status": "fetch_complete", "cache": audit_cache.status()})
                return

        # ── Step 3: LLM analysis ──
        # When action=analyze, read from cache
        if action == AuditAction.ANALYZE:
            if not audit_cache.has_data():
                yield _sse(
                    {"status": "error", "step": "llm", "message": "No cached data. Run 'Get AdGuard data' first."})
                return
            cleaned = audit_cache.cleaned_data
            # Show the cached clean step as already done
            yield _sse({
                "status": "clean_done",
                "allowed": audit_cache.allowed_count,
                "blocked": audit_cache.blocked_count,
                "model": model_services.value,
                "from_cache": True,
            })

        try:
            active_rules_text = prompt_rules_service.get_active_rules_text()
            final_prompt = f"{active_rules_text}\n\n{user_prompt}".strip() if user_prompt or active_rules_text else ""

            yield _sse({"status": "llm_thinking", "model": model_services.value})

            if model_services == ModelServices.VERTEX_AI:
                result = await loop.run_in_executor(
                    _executor,
                    lambda: vertex_ai.generate(str(cleaned), user_prompt=final_prompt)
                )
            elif model_services == ModelServices.DEEPSEEK:
                result = await loop.run_in_executor(
                    _executor,
                    lambda: deepseek.generate(str(cleaned), user_prompt=final_prompt)
                )
            else:
                result = await loop.run_in_executor(
                    _executor,
                    lambda: gemini.generate(str(cleaned), user_prompt=final_prompt)
                )

            if isinstance(result, dict) and "error" in result:
                yield _sse({"status": "error", "step": "llm", "message": result["error"]})
                return

            yield _sse({"status": "complete", "result": result})

        except Exception as e:
            log.error(f"[audit/stream] LLM error: {e}")
            yield _sse({"status": "error", "step": "llm", "message": str(e)})
            return

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/audit/cache")
def get_audit_cache():
    """Return the current cache status."""
    return audit_cache.status()


@router.post("/audit/cache/clear")
def clear_audit_cache():
    """Clear the cached cleaned data."""
    audit_cache.clear()
    return {"status": "cleared"}


def _sse(data: dict) -> str:
    """Format a dict as an SSE 'data:' line."""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


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


@router.post("/to_delete")
def to_delete(data: DomainNamesRequest):
    """Delete selected user rules entirely (manual action from Current Rules)."""
    ctrl = controller.DataController()
    optimized_rules = ctrl.get_actual_filter()

    final_raw_rules, stats = analysis_service.apply_delete_to_rules(optimized_rules, data.domains)

    success = ctrl.set_actual_filter(final_raw_rules)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to save rules in AdGuard")

    return {
        "status": "success",
        "action": "delete",
        "stats": stats,
        "message": f"Deleted {stats['deleted']} rule(s)."
    }


@router.get("/get_actual_filter")
def get_actual_filter() -> OptimizedRulesSet:
    ctrl = controller.DataController()
    log.debug(f"[audit][get_actual_filter] -> start")
    return ctrl.get_actual_filter()
