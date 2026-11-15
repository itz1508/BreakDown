"""Stdin/stdout JSON envelope for skill processes, on the standard library.

One request is read from stdin as a single JSON document; exactly one JSON
response is written to stdout. Diagnostics go to stderr. Exit codes carry
success: a non-zero exit means the response reported failure or the process
crashed before responding.
"""

from __future__ import annotations

import json
import sys
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Request(BaseModel):
    """One work request, composed by the delegating layer and read from stdin."""

    model_config = ConfigDict(frozen=True)

    todo_id: str = Field(min_length=1)
    todo_revision: int = Field(ge=1)
    exec_id: str = Field(min_length=1)
    skill: str = Field(min_length=1)
    action: str = Field(min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)
    workspace: str = Field(min_length=1)
    state_root: str = Field(min_length=1)


class Response(BaseModel):
    """Exactly one response document; ``ok`` false carries a typed error."""

    model_config = ConfigDict(frozen=True)

    ok: bool
    result: dict[str, Any] = Field(default_factory=dict)
    error: dict[str, Any] | None = None


def read_request(stream: Any = None) -> Request:
    """Read and validate one request document from stdin."""
    raw = (sys.stdin if stream is None else stream).read()
    data = json.loads(raw)
    return Request.model_validate(data)


def write_response(response: Response, stream: Any = None) -> None:
    """Write exactly one JSON response document followed by a newline."""
    out = sys.stdout if stream is None else stream
    out.write(json.dumps(response.model_dump(mode="json")))
    out.write("\n")
    out.flush()


def ok_response(result: dict[str, Any] | None = None) -> Response:
    return Response(ok=True, result=result or {})


def error_response(code: str, message: str) -> Response:
    return Response(ok=False, error={"code": code, "message": message})
