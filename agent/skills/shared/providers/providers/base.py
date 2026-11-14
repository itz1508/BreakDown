"""Provider adapter base — protocol, request/result types, capabilities."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ProviderError(Exception):
    pass


class ProviderRequest(BaseModel):
    run_id: str = Field(min_length=1)
    prompt: str = Field(min_length=1)
    system_prompt: str = ""
    messages: tuple[dict[str, Any], ...] = ()
    tools: tuple[dict[str, Any], ...] = ()
    tool_choice: str | None = None
    max_tokens: int = Field(default=4096, ge=1)
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def check_tool_request(self) -> ProviderRequest:
        if self.tool_choice is not None and not self.tools:
            raise ValueError("tool_choice requires tools")
        return self


class ProviderResult(BaseModel):
    content: str = ""
    tool_calls: tuple[dict[str, Any], ...] = ()
    finish_reason: str = "stop"
    usage: dict[str, Any] = Field(default_factory=dict)
    provider: str = ""
    model: str = ""
    model_config = ConfigDict(extra="forbid")
