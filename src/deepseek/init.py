# Please install OpenAI SDK first: `pip3 install openai`
import json
import time

import openai
from openai import OpenAI

from src.adguard_auditor.core import prompts
from src.adguard_auditor.core.config import settings
from src.adguard_auditor.core.logger import log


def _parse_json_response(raw_text: str) -> dict:
    """
    Extract a valid JSON object from a model response that might be wrapped
    in markdown code fences (```json ... ```) or contain extra whitespace.
    """
    text = raw_text.strip()
    # Remove markdown code block if present
    if text.startswith("```"):
        # Find the first newline and remove the opening fence
        text = text.split("\n", 1)[-1] if "\n" in text else ""
        # Remove closing fence
        if text.endswith("```"):
            text = text[:-3].strip()
    return json.loads(text)


def generate(log_data: str, user_prompt: str = "") -> dict:
    client = OpenAI(
        api_key=settings.DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com"
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

    # Final system prompt with DeepSeek-expected JSON structure
    # (The FIRST_SYSTEM_PROMPT should already contain detailed JSON output instructions)
    system_prompt = prompts.FIRST_SYSTEM_PROMPT.format(
        user_context_section=user_context_section
    )
    system_prompt = f"{system_prompt}\n{prompts.DEEPSEEK_STRUCTURE_PROMT}"
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Here is the AdGuard JSON log to analyze:\n\n{log_data}"}
    ]

    # DeepSeek-specific generation parameters (can be extended via settings)
    generate_params = {
        # "temperature": 0.2,
        # "max_tokens": 8000,
        "response_format": {"type": "json_object"},
    }

    # Optional reasoning settings (DeepSeek advanced features)
    # Use them only if the model supports them; you can guard with settings flags.
    if getattr(settings, "DEEPSEEK_REASONING_EFFORT", None):
        generate_params["reasoning_effort"] = settings.DEEPSEEK_REASONING_EFFORT
    else:
        generate_params["reasoning_effort"] = "high"

    if getattr(settings, "DEEPSEEK_THINKING_ENABLED", True):
        generate_params["extra_body"] = {"thinking": {"type": "enabled"}}
    else:
        generate_params["extra_body"] = {"thinking": {"type": "disabled"}}

    max_attempts_per_model = 2
    models = settings.DEEPSEEK_MODELS_NAME

    for model in models:
        log.info(f"Trying to use model: {model}...")
        for attempt in range(1, max_attempts_per_model + 1):
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    **generate_params
                )
                # DeepSeek may include reasoning_content – we only need the final content
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

                log.info(f"Successfully generated response using {model}")
                log.debug(f"Response generated response using {model} its \n{parsed}\n and raw_output = \n{raw_output}")
                return parsed

            except openai.RateLimitError as e:
                log.warning(f"Model {model} rate limited (HTTP {e.status_code}). "
                            f"Attempt {attempt}/{max_attempts_per_model}.")
                if attempt < max_attempts_per_model:
                    time.sleep(10)
                    continue
                else:
                    log.warning(f"Exhausted attempts for {model}. Switching to next model...")
                    break

            except openai.APIError as e:
                # Covers 503, 500, etc.
                log.error(f"API Error with model {model}: {e}")
                if attempt < max_attempts_per_model:
                    time.sleep(5)
                    continue
                break

            except (json.JSONDecodeError, ValueError) as e:
                log.warning(f"Model {model} returned invalid/unparseable JSON: {e}. "
                            f"Attempt {attempt}/{max_attempts_per_model}.")
                # Possibly retry with same model if JSON was malformed
                if attempt < max_attempts_per_model:
                    continue
                else:
                    log.warning(f"Exhausted attempts for {model}. Switching to next model...")
                    break

            except Exception as e:
                log.error(f"Unexpected error with model {model}: {e}")
                break

    log.error("All DeepSeek models failed or returned unparseable output.")
    return {"error": "All DeepSeek models failed or rate limited. Please try again later."}
