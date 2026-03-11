# pip install openai

import json
from openai import OpenAI
from src.adguard_auditor.core.config import settings
from src.adguard_auditor.core import prompts


client = OpenAI(api_key=settings.OPENAI_API_KEY)


def generate(log_data: str):

    response_schema = {
        "type": "object",
        "required": [
            "domains_to_block",
            "domains_to_unblock",
            "domains_to_test",
            "analysis_summary"
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
                        "reason": {
                            "type": "string",
                            "description": "Why this should be blocked"
                        },
                        "confidence": {
                            "type": "string",
                            "description": "HIGH, MEDIUM, or LOW"
                        }
                    }
                }
            },

            "domains_to_unblock": {
                "type": "array",
                "description": "Blocked domains that are false positives.",
                "items": {
                    "type": "object",
                    "required": ["domain", "reason", "confidence"],
                    "properties": {
                        "domain": {"type": "string"},
                        "reason": {
                            "type": "string",
                            "description": "Why this should be unblocked"
                        },
                        "confidence": {
                            "type": "string",
                            "description": "HIGH, MEDIUM, or LOW"
                        }
                    }
                }
            },

            "domains_to_test": {
                "type": "array",
                "description": "Suspicious domains that require manual testing.",
                "items": {
                    "type": "object",
                    "required": ["domain", "reason"],
                    "properties": {
                        "domain": {"type": "string"},
                        "reason": {
                            "type": "string",
                            "description": "Why this domain is ambiguous"
                        }
                    }
                }
            },

            "analysis_summary": {
                "type": "string",
                "description": "Summary of network traffic health"
            }

        }
    }

    stream = client.responses.stream(
        model=settings.OPENAI_MODEL_NAME,  # например "gpt-5-mini" или "gpt-4.1"
        input=[
            {
                "role": "system",
                "content": prompts.FIRST_SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": f"Here is the AdGuard JSON log to analyze:\n\n{log_data}"
            }
        ],
        temperature=0.2,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "adguard_analysis",
                "schema": response_schema
            }
        }
    )

    response_text = ""

    for event in stream:
        if event.type == "response.output_text.delta":
            print(event.delta, end="")
            response_text += event.delta

    print()

    return json.loads(response_text)