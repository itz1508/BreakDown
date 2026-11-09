"""Builder skill entry point.

Run: uv run --no-sync python -m agent.skills.builder.run <repository-root>
"""

from __future__ import annotations

from agent.contracts.host import HostDispatchEnvelope, HostDispatchResult


def main() -> None:
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m agent.skills.builder.run <repository-root>")
        sys.exit(1)

    repo_root = sys.argv[1]

    # Demonstrate builder capabilities
    print("Builder skill - effect execution and verification")
    print(f"Repository root: {repo_root}")


if __name__ == "__main__":
    main()


# --- PRE/POST dispatch for Runtime integration ---
# The Builder skill executes admitted Build actions and reports effects.


def pre_dispatch(request: HostDispatchEnvelope) -> HostDispatchEnvelope:
    """Validate and enrich the request before Builder execution."""
    if request.stage not in ("build", "build_validation"):
        raise ValueError(
            f"Builder skill can only operate at stages 'build' or 'build_validation', got '{request.stage}'."
        )
    if request.requester_role not in ("host", "builder"):
        raise ValueError(f"Builder skill rejects requests from unauthorized role '{request.requester_role}'.")
    enriched = request.model_copy(
        update={
            "information_needed": (
                request.information_needed + " | builder_scope: admitted_build_action_execution_effect_reporting"
            )
        }
    )
    return enriched


def post_dispatch(result: HostDispatchResult) -> HostDispatchResult:
    """Verify Builder result after execution."""
    if not result.output_ref.artifact_id:
        raise ValueError("Builder result must reference an output artifact.")
    if result.output_ref.contract_id != "build_record":
        raise ValueError(f"Builder output must use contract 'build_record', got '{result.output_ref.contract_id}'.")
    return result


__all__ = ["post_dispatch", "pre_dispatch"]
