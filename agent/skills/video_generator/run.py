"""Video Generator skill entry point.

Run: uv run --no-sync python -m agent.skills.video_generator.run <repository-root>
Belt: belt login && belt app run google/veo-3-1-fast --input '{"prompt":"..."}'
"""

from __future__ import annotations

import sys
from pathlib import Path

from agent.contracts.host import HostDispatchEnvelope, HostDispatchResult


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python -m agent.skills.video_generator.run <repository-root>")
        sys.exit(1)
    repo_root = Path(sys.argv[1])
    if not repo_root.exists():
        print(f"Repository root not found: {repo_root}")
        sys.exit(1)
    print("Video Generator skill — 40+ models via belt CLI")
    print(f"Repository root: {repo_root}")
    print("Run `belt app list --category video` to browse models")
    # Dispatch is host-driven; this CLI is for local inspection only
    print("Use: belt app run <app-id> --input '<json>'")


# --- PRE/POST dispatch for Runtime integration ---


def pre_dispatch(request: HostDispatchEnvelope) -> HostDispatchEnvelope:
    """Validate and enrich before video generation."""
    if request.stage not in ("build", "research", "planning"):
        raise ValueError(f"Video Generator stage must be build/research/planning, got '{request.stage}'")
    if request.requester_role not in ("host", "video_generator", "builder"):
        raise ValueError(f"Unauthorized role '{request.requester_role}' for video generation")
    enriched = request.model_copy(
        update={
            "information_needed": (
                request.information_needed + " | video_scope: belt_app_execution_text_image_avatar_edit_upscale_foley"
            )
        }
    )
    return enriched


def post_dispatch(result: HostDispatchResult) -> HostDispatchResult:
    """Verify video result."""
    if not result.output_ref.artifact_id:
        raise ValueError("Video result must reference output artifact")
    if result.output_ref.contract_id not in ("video_record", "build_record"):
        raise ValueError(
            f"Video output contract must be video_record/build_record, got '{result.output_ref.contract_id}'"
        )
    return result


__all__ = ["main", "post_dispatch", "pre_dispatch"]
