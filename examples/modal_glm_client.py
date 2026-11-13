"""Streaming client example for the low-cost Modal GLM deployment.

Targets the ``ep-glm-5-3-flash-nvfp4-server`` Modal function, which serves
``nvidia/GLM-5.3-Flash-NVFP4`` behind the same OpenAI-compatible API used by
the Qwen deployment: streaming, strict JSON schema, tools, and reasoning.
Verified live on 2026-11-11 (strict JSON reply, reasoning tokens reported).

Credentials are read from the environment only — never hardcode them:
- ``MODAL_PROXY_TOKEN_ID`` + ``MODAL_PROXY_TOKEN_SECRET``, composed as
  ``"<id>.<secret>"`` for proxy-auth deployments, or
- ``MODAL_API_KEY`` holding a Modal web key (``wk-...``).

Run: ``python examples/modal_glm_client.py``
"""

from __future__ import annotations

import os
import sys

from openai import OpenAI

BASE_URL = "https://cs1508-4ever-oneshot--ep-glm-5-3-flash-nvfp4-server.us-west.modal.direct/v1"
MODEL = "nvidia/GLM-5.3-Flash-NVFP4"

PERSON_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer"},
        "city": {"type": "string"},
    },
    "required": ["name", "age", "city"],
    "additionalProperties": False,
}

WEATHER_TOOL = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get the current weather for a city.",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
    },
}


def resolve_api_key() -> str:
    """Compose the bearer key from environment credentials."""
    token_id = os.environ.get("MODAL_PROXY_TOKEN_ID")
    token_secret = os.environ.get("MODAL_PROXY_TOKEN_SECRET")
    if token_id and token_secret:
        return f"{token_id}.{token_secret}"
    key = os.environ.get("MODAL_API_KEY")
    if key:
        return key
    raise SystemExit("Set MODAL_PROXY_TOKEN_ID/MODAL_PROXY_TOKEN_SECRET or MODAL_API_KEY")


def main() -> int:
    client = OpenAI(base_url=BASE_URL, api_key=resolve_api_key())
    stream = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a concise technical assistant."},
            {"role": "user", "content": "Extract the name, age, and city: Ada, 36, London."},
        ],
        temperature=0.3,
        max_tokens=2048,
        top_p=0.9,
        stream=True,
        response_format={
            "type": "json_schema",
            "json_schema": {"name": "person_info", "strict": True, "schema": PERSON_SCHEMA},
        },
        tools=[WEATHER_TOOL],
        tool_choice="auto",
        extra_body={"reasoning": {"enabled": True}},
    )
    for chunk in stream:
        if not chunk.choices:
            continue  # terminal/usage chunks carry no choices on this endpoint
        delta = chunk.choices[0].delta.content
        if delta:
            print(delta, end="", flush=True)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
