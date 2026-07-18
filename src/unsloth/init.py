# Connect to a locally-running Unsloth server (OpenAI-compatible endpoint).
# pip install openai
import json
import time

import openai
from openai import OpenAI

from src.adguard_auditor.core import prompts
from src.adguard_auditor.core.config import settings
from src.adguard_auditor.core.logger import log


# JSON Schema constraining the model output. Passed with strict=True so Unsloth
# enforces it during decoding instead of relying on the model to comply.
RESPONSE_SCHEMA = {
    "type": "object",
    "required": [
        "domains_to_block",
        "domains_to_unblock",
        "domains_to_test",
        "analysis_summary",
    ],
    "properties": {
        "domains_to_block": {
            "type": "array",
            "description": "Allowed domains that should be blocked (ads, telemetry, trackers).",
            "items": {
                "type": "object",
                "required": ["domain", "reason", "confidence"],
                "properties": {
                    "domain": {"type": "string"},
                    "reason": {"type": "string", "description": "Why this should be blocked"},
                    "confidence": {"type": "string", "description": "HIGH, MEDIUM, or LOW"},
                },
                "additionalProperties": False,
            },
        },
        "domains_to_unblock": {
            "type": "array",
            "description": "Blocked domains that are false positives and should be unblocked to prevent app breakage.",
            "items": {
                "type": "object",
                "required": ["domain", "reason", "confidence"],
                "properties": {
                    "domain": {"type": "string"},
                    "reason": {"type": "string", "description": "Why this should be unblocked"},
                    "confidence": {"type": "string", "description": "HIGH, MEDIUM, or LOW"},
                },
                "additionalProperties": False,
            },
        },
        "domains_to_test": {
            "type": "array",
            "description": "Suspicious or mixed-use domains that require manual testing before blocking.",
            "items": {
                "type": "object",
                "required": ["domain", "reason"],
                "properties": {
                    "domain": {"type": "string"},
                    "reason": {"type": "string", "description": "Why this domain is ambiguous"},
                },
                "additionalProperties": False,
            },
        },
        "analysis_summary": {
            "type": "string",
            "description": "A brief summary of the overall network traffic health based on the logs.",
        },
    },
    "additionalProperties": False,
}


def _parse_json_response(raw_text: str) -> dict:
    """
    Extract a valid JSON object from a model response that might be wrapped
    in markdown code fences (```json ... ```) or contain extra whitespace.
    Local GGUF models often wrap their output in fences even under strict mode.
    """
    text = raw_text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1] if "\n" in text else ""
        if text.endswith("```"):
            text = text[:-3].strip()
    return json.loads(text)


def generate(log_data: str, user_prompt: str = "") -> dict:
    client = OpenAI(
        base_url=settings.UNSLOTH_BASE_URL,   # e.g. http://localhost:8888/v1
        api_key=settings.UNSLOTH_API_KEY,     # your sk-unsloth-… key
    )

    # Build user context section for the system prompt
    if user_prompt.strip():
        user_context_section = f"""
    USER PREFERENCES AND OVERRIDES (STRICTLY FOLLOW THESE):
    The user has provided the following specific instructions regarding certain domains or services.
    Prioritize these instructions over your default logic:
    "{user_prompt}"
    """
    else:
        user_context_section = ""

    system_prompt = prompts.FIRST_SYSTEM_PROMPT.format(
        user_context_section=user_context_section
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Here is the AdGuard JSON log to analyze:\n\n{log_data}"},
    ]

    generate_params = {
        "temperature": 0.2,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "adguard_analysis",
                "schema": RESPONSE_SCHEMA,
                "strict": True,
            },
        },
    }

    max_attempts_per_model = 2
    models = settings.UNSLOTH_MODELS_NAME

    for model in models:
        log.info(f"Trying to use Unsloth model: {model}...")
        for attempt in range(1, max_attempts_per_model + 1):
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    **generate_params,
                )
                raw_output = response.choices[0].message.content
                if not raw_output:
                    raise ValueError("Empty response from model")

                parsed = _parse_json_response(raw_output)

                usage = getattr(response, "usage", None)
                if usage is not None:
                    parsed["_usage"] = {
                        "prompt_tokens": getattr(usage, "prompt_tokens", None),
                        "completion_tokens": getattr(usage, "completion_tokens", None),
                        "total_tokens": getattr(usage, "total_tokens", None),
                    }

                log.info(f"Successfully generated response using Unsloth {model}")
                log.debug(f"Response generated using {model} its \n{parsed}\n and raw_output = \n{raw_output}")
                return parsed

            except openai.RateLimitError as e:
                log.warning(f"Unsloth model {model} rate limited (HTTP {e.status_code}). "
                            f"Attempt {attempt}/{max_attempts_per_model}.")
                if attempt < max_attempts_per_model:
                    time.sleep(10)
                    continue
                else:
                    log.warning(f"Exhausted attempts for {model}. Switching to next model...")
                    break

            except openai.APIConnectionError as e:
                # Local server not running / wrong port / wrong base_url.
                log.error(f"Cannot reach Unsloth server at {settings.UNSLOTH_BASE_URL}: {e}")
                if attempt < max_attempts_per_model:
                    time.sleep(5)
                    continue
                break

            except openai.APIError as e:
                # Covers 503, 500, etc.
                log.error(f"Unsloth API Error with model {model}: {e}")
                if attempt < max_attempts_per_model:
                    time.sleep(5)
                    continue
                break

            except (json.JSONDecodeError, ValueError) as e:
                log.warning(f"Unsloth model {model} returned invalid/unparseable JSON: {e}. "
                            f"Attempt {attempt}/{max_attempts_per_model}.")
                if attempt < max_attempts_per_model:
                    continue
                else:
                    log.warning(f"Exhausted attempts for {model}. Switching to next model...")
                    break

            except Exception as e:
                log.error(f"Unexpected error with Unsloth model {model}: {e}")
                break

    log.error("All Unsloth models failed or returned unparseable output.")
    return {"error": "All Unsloth models failed or unreachable. Please check the local server."}
