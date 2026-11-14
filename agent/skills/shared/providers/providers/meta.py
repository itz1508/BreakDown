"""Meta Muse Spark provider — OpenAI-compatible SDK with credential hygiene."""

from __future__ import annotations

import os
from typing import Any

from agent.skills.shared.providers.providers.base import (
    CapabilityDescriptor,
    ProviderError,
    ProviderRequest,
    ProviderResult,
)


class MetaProvider:
    """Meta Muse Spark provider adapter.

    Uses the OpenAI Python SDK with Meta's compatible endpoint.
    Credentials are read at call time from the environment — never persisted.
    """

    PROVIDER_NAME = "meta"
    DEFAULT_BASE_URL = "https://api.meta.ai/v1"
    DEFAULT_MODEL = "muse-spark-1.3"

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        credential_ref: str = "MODEL_API_KEY",
    ) -> None:
        self._base_url = base_url or os.environ.get("META_MODEL_BASE_URL") or self.DEFAULT_BASE_URL
        self._model = model or os.environ.get("META_MODEL_ID") or self.DEFAULT_MODEL
        self._credential_ref = credential_ref
        self._client: Any = None

    def _get_client(self) -> Any:
        """Lazy import and client creation at call time."""
        if self._client is not None:
            return self._client
        try:
            from openai import OpenAI
        except ImportError as e:
            raise ProviderError("openai SDK not installed (pip install 'oneshot[meta]')") from e
        key = os.environ.get(self._credential_ref)
        if not key:
            raise ProviderError(f"environment variable {self._credential_ref} not set")
        self._client = OpenAI(api_key=key, base_url=self._base_url)
        return self._client

    @staticmethod
    def _tool_call_dict(call: Any) -> dict[str, Any]:
        """Normalize one SDK tool call into the provider-neutral result shape."""
        function = getattr(call, "function", None)
        return {
            "id": getattr(call, "id", ""),
            "type": getattr(call, "type", "function"),
            "function": {
                "name": getattr(function, "name", ""),
                "arguments": getattr(function, "arguments", ""),
            },
        }

    def generate(self, request: ProviderRequest) -> ProviderResult:
        """Generate using Meta Muse Spark, optionally with tool definitions."""
        client = self._get_client()
        if request.messages:
            messages: list[dict[str, Any]] = [dict(message) for message in request.messages]
        else:
            messages = []
            if request.system_prompt:
                messages.append({"role": "system", "content": request.system_prompt})
            messages.append({"role": "user", "content": request.prompt})
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
        }
        if request.tools:
            payload["tools"] = [dict(tool) for tool in request.tools]
            if request.tool_choice is not None:
                payload["tool_choice"] = request.tool_choice
        response = client.chat.completions.create(**payload)
        choice = response.choices[0]
        message = choice.message
        return ProviderResult(
            content=message.content or "",
            tool_calls=tuple(self._tool_call_dict(call) for call in (message.tool_calls or ())),
            finish_reason=choice.finish_reason or "stop",
            usage=(
                {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0,
                }
                if response.usage
                else {}
            ),
            provider=self.PROVIDER_NAME,
            model=self._model,
        )

    def declared_capabilities(self) -> CapabilityDescriptor:
        return CapabilityDescriptor(
            structured_outputs=True,
            streaming=True,
            batch=False,
            prompt_caching=False,
            strict_tool_schemas=True,
        )
