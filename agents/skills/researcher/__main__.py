"""Researcher stdin entrypoint: python -m agents.skills.researcher < request.json"""

from __future__ import annotations

from pathlib import Path

from agents.shared.io import error_response, ok_response, read_request, write_response
from agents.skills.researcher.researching import ResearchContext, ResearchRequest, execute
from agents.skills.shared.providers.base import ProviderError
from system.storage.artifact_store import ArtifactStore


def main() -> int:
    try:
        request = read_request()
    except Exception as exc:  # malformed stdin is an error response, not a crash
        write_response(error_response("invalid_request", f"{type(exc).__name__}: {exc}"))
        return 1
    try:
        state_root = Path(request.state_root)
        context = ResearchContext(
            workspace_root=Path(request.workspace),
            artifact_store=ArtifactStore(state_root),
            providers=None,
        )
        research = ResearchRequest(
            task_id=request.todo_id,
            run_id=f"{request.todo_id}-{request.exec_id[:8]}",
            information_needed=str(request.payload.get("information_needed", request.todo_id)),
            input_text=str(request.payload.get("input_text", request.payload.get("information_needed", ""))),
        )
        result = execute(context, research)
        write_response(ok_response(result))
        return 0
    except ProviderError as exc:
        write_response(error_response("provider_unavailable", str(exc)))
        return 1
    except Exception as exc:  # the process boundary is the error surface
        write_response(error_response("researcher_failed", f"{type(exc).__name__}: {exc}"))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
