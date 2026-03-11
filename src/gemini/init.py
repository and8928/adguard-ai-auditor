# To run this code you need to install the following dependencies:
# pip install google-genai
import os
import json
from google import genai
from google.genai import types
from google.genai.errors import APIError
from src.adguard_auditor.core.config import settings
from src.adguard_auditor.core import prompts
from src.adguard_auditor.core.logger import log


def generate(log_data: str):
    client = genai.Client(
        api_key=settings.GEMINI_API_KEY,
    )

    # Настройка схемы ответа (JSON Schema)
    response_schema = genai.types.Schema(
        type=genai.types.Type.OBJECT,
        required=["domains_to_block", "domains_to_unblock", "domains_to_test", "analysis_summary"],
        properties={
            "domains_to_block": genai.types.Schema(
                type=genai.types.Type.ARRAY,
                description="Allowed domains that should be blocked (ads, telemetry, trackers).",
                items=genai.types.Schema(
                    type=genai.types.Type.OBJECT,
                    required=["domain", "reason", "confidence"],
                    properties={
                        "domain": genai.types.Schema(type=genai.types.Type.STRING),
                        "reason": genai.types.Schema(type=genai.types.Type.STRING,
                                                     description="Why this should be blocked"),
                        "confidence": genai.types.Schema(type=genai.types.Type.STRING,
                                                         description="HIGH, MEDIUM, or LOW")
                    }
                )
            ),
            "domains_to_unblock": genai.types.Schema(
                type=genai.types.Type.ARRAY,
                description="Blocked domains that are false positives and should be unblocked to prevent app breakage.",
                items=genai.types.Schema(
                    type=genai.types.Type.OBJECT,
                    required=["domain", "reason", "confidence"],
                    properties={
                        "domain": genai.types.Schema(type=genai.types.Type.STRING),
                        "reason": genai.types.Schema(type=genai.types.Type.STRING,
                                                     description="Why this should be unblocked"),
                        "confidence": genai.types.Schema(type=genai.types.Type.STRING,
                                                         description="HIGH, MEDIUM, or LOW")
                    }
                )
            ),
            "domains_to_test": genai.types.Schema(
                type=genai.types.Type.ARRAY,
                description="Suspicious or mixed-use domains that require manual testing before blocking.",
                items=genai.types.Schema(
                    type=genai.types.Type.OBJECT,
                    required=["domain", "reason"],
                    properties={
                        "domain": genai.types.Schema(type=genai.types.Type.STRING),
                        "reason": genai.types.Schema(type=genai.types.Type.STRING,
                                                     description="Why this domain is ambiguous")
                    }
                )
            ),
            "analysis_summary": genai.types.Schema(
                type=genai.types.Type.STRING,
                description="A brief summary of the overall network traffic health based on the logs."
            ),
        },
    )

    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=f"Here is the AdGuard JSON log to analyze:\n\n{log_data}"),
            ],
        ),
    ]

    generate_content_config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(
            thinking_level="HIGH",
        ),
        response_mime_type="application/json",
        response_schema=response_schema,
        system_instruction=[
            types.Part.from_text(text=prompts.FIRST_SYSTEM_PROMPT),
        ],
        temperature=0.2,
    )
    for model in settings.GEMINI_MODELS_NAME:
        log.info(f"Trying to use model: {model}...")
        try:
            result = generate_content(client, contents, generate_content_config, model)
            log.info(f"Successfully generated response using {model}")
            return result

        except APIError as e:
            if e.code == 429:  # Too Many Requests
                log.warning(f"Model {model} rate limited (429). Switching to the next model...")
                continue
            else:
                log.error(f"API Error with model {model}: {e}")
                raise e

        except json.JSONDecodeError as e:
            log.warning(f"Model {model} returned invalid JSON: {e}. Trying next model...")
            continue
        except Exception as e:
            log.error(f"Unexpected error with model {model}: {e}")
            raise e
    log.error("All Gemini models failed or rate limited.")
    return {"error": "All models failed or rate limited. Please try again later."}

def generate_content(client: genai.Client, contents: list, generate_content_config: types.GenerateContentConfig, model: str):
    """
    """
    response_text = ""
    for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
    ):
        response_text += chunk.text
        # print(chunk.text, end="") # debug

    return json.loads(response_text)


# if __name__ == "__main__":
#     # sample
#     sample_log = """
#     {
#       "Allowed": [
#         {"domain": "blowfish-blocklist-proxy.phantom.app", "filterId": ""},
#         {"domain": "calendar.google.com", "filterId": ""},
#         {"domain": "mtalk.google.com", "filterId": ""}
#       ],
#       "Blocked": [
#         {"domain": "mobile.events.data.microsoft.com", "filterId": 1769870455},
#         {"domain": "client.wns.windows.com", "filterId": 0},
#         {"domain": "s.youtube.com", "filterId": 1769870455}
#       ]
#     }
#     """
#
#     result = generate(sample_log)
#     print(json.dumps(result, indent=2, ensure_ascii=False))
