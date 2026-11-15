"""Coder stdin entrypoint: python -m agents.skills.coder < request.json"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from pydantic import TypeAdapter

from agents.skills.auditor.contracts._discovery import CodeDesign
from agents.skills.coder.coding import DesignQuestion, review_questions

_DESIGN_ADAPTER = TypeAdapter(CodeDesign)


def main() -> int:
    from agents.shared.io import error_response, ok_response, read_request, write_response

    try:
        request = read_request()
    except Exception as exc:  # malformed stdin is an error response, not a crash
        write_response(error_response("invalid_request", f"{type(exc).__name__}: {exc}"))
        return 1
    try:
        design: Any = _DESIGN_ADAPTER.validate_python(request.payload.get("design", {}))
        questions: tuple[DesignQuestion, ...] = review_questions(design)
        write_response(ok_response({"questions": [asdict(q) for q in questions]}))
        return 0
    except Exception as exc:  # the process boundary is the error surface
        write_response(error_response("coder_failed", f"{type(exc).__name__}: {exc}"))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
