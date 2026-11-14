"""Researcher search loop against real local tools and storage.

The model is scripted: these tests prove the loop, validation, result states and
artifact persistence, not live-model quality. The tool calls and the evidence
digests they produce are real.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent.skills.researcher.contracts.research import (
    FixtureSpecification,
    InformationClass,
    ResearchRecord,
)
from agent.skills.researcher.researching import (
    MAX_STEPS,
    MAX_TOOL_CALLS,
    ResearchSearchResult,
    run,
    search,
)
from agent.skills.shared.host.skill_dispatch import ResearchArguments, SkillContext
from agent.skills.shared.host.sys_controller import STAGE_ORDER, HostController
from agent.skills.shared.providers.base import ProviderError, ProviderRequest, ProviderResult
from agent.skills.spec_search.spec_searching import SpecQuery
from agent.skills.spec_search.spec_searching import search as spec_search
from tests.e2e.harness import advance, create_task

pytestmark = pytest.mark.e2e

TASK_ID = "task-research"
RUN_ID = "run-research"
NOTES = "# Notes\n\ncheckpoint_cas guards the store.\n\nOtherwise nothing.\n"


class ScriptedProvider:
    """Deterministic stand-in for the model call; records every request."""

    def __init__(self, results: list[ProviderResult]) -> None:
        self._results = list(results)
        self.requests: list[ProviderRequest] = []

    def generate(self, request: ProviderRequest) -> ProviderResult:
        self.requests.append(request)
        if not self._results:
            raise AssertionError("scripted provider exhausted")
        return self._results.pop(0)


class ScriptedRegistry:
    default_provider = "scripted"

    def __init__(self, provider: ScriptedProvider) -> None:
        self.provider = provider

    def generate(self, key: str, request: ProviderRequest) -> ProviderResult:
        assert key == self.default_provider
        return self.provider.generate(request)


def tool_call(call_id: str, name: str, arguments: dict[str, object]) -> dict[str, object]:
    return {
        "id": call_id,
        "type": "function",
        "function": {"name": name, "arguments": json.dumps(arguments)},
    }


def tool_results(*calls: dict[str, object]) -> ProviderResult:
    return ProviderResult(content="", tool_calls=tuple(calls), finish_reason="tool_calls")


def final_answer(payload: dict[str, object], finish_reason: str = "stop") -> ProviderResult:
    return ProviderResult(content=json.dumps(payload), finish_reason=finish_reason)


def dispatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    results: list[ProviderResult],
    *,
    workspace: Path | None = None,
) -> tuple[HostController, SkillContext, object, ScriptedProvider]:
    workspace = workspace or make_workspace(tmp_path)
    host = HostController(tmp_path / "state", workspace)
    input_ref = create_task(host, TASK_ID, RUN_ID, "Locate checkpoint_cas")
    for stage in STAGE_ORDER[:6]:
        advance(host, TASK_ID, RUN_ID, stage)
    envelope, _, _ = host.prepare_agent_dispatch(
        TASK_ID, input_ref, "Locate checkpoint_cas usage", requested_role="researcher"
    )
    provider = ScriptedProvider(results)
    monkeypatch.setattr(host, "providers", ScriptedRegistry(provider))
    return host, SkillContext.from_host(host, workspace), envelope, provider


def make_workspace(tmp_path: Path) -> Path:
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "notes.md").write_text(NOTES, encoding="utf-8")
    return workspace


def failing_registry() -> object:
    class _Failing:
        default_provider = "meta"

        def generate(self, key: str, request: ProviderRequest) -> ProviderResult:
            raise ProviderError("environment variable MODEL_API_KEY not set")

    return _Failing()


def test_loop_uses_real_search_and_persists_three_artifacts(tmp_path, monkeypatch) -> None:
    workspace = make_workspace(tmp_path)
    hit = spec_search(workspace, SpecQuery(terms=("checkpoint_cas",))).hits[0]
    results = [
        tool_results(tool_call("c1", "search_repository", {"terms": ["checkpoint_cas"]})),
        final_answer(
            {
                "findings": [
                    {"statement": "checkpoint_cas guards the store", "evidence_digests": [hit.snippet_digest]}
                ],
                "constraints": ["store owns compare-and-swap"],
                "unknowns": ["no web evidence"],
            }
        ),
    ]
    host, context, envelope, provider = dispatch(tmp_path, monkeypatch, results, workspace=workspace)

    outcome: ResearchSearchResult = search(context, envelope, ResearchArguments())

    assert outcome.outcome == "completed"
    assert set(outcome.artifacts) == {"audit", "code", "fixture"}
    assert outcome.calls[0].status == "ok"
    assert outcome.findings[0].information_class is InformationClass.VERIFIED_EVIDENCE

    audit_ref = outcome.artifacts["audit"]
    assert host.artifact_store.get_digest(str(audit_ref["artifact_id"]), 1) == audit_ref["artifact_digest"]
    audit = ResearchRecord.model_validate_json(host.artifact_store.get_verified(str(audit_ref["artifact_id"]), 1))
    assert audit.claims[0].evidence_refs == (hit.snippet_digest,)
    assert audit.evidence[0].location == f"{hit.path}:{hit.line}"
    assert audit.evidence[0].content_digest == hit.snippet_digest

    fixture = FixtureSpecification.model_validate_json(
        host.artifact_store.get_verified(str(outcome.artifacts["fixture"]["artifact_id"]), 1)
    )
    assert fixture.required_evidence == (hit.snippet_digest,)

    history = provider.requests[-1].messages
    assert any(message.get("role") == "tool" and message.get("tool_call_id") == "c1" for message in history)
    assert any(message.get("role") == "assistant" and message.get("tool_calls") for message in history)
    assert provider.requests[0].tools


def test_unknown_tool_bad_arguments_and_escapes_are_recorded(tmp_path, monkeypatch) -> None:
    (tmp_path / "outside.md").write_text("outside the workspace\n", encoding="utf-8")
    results = [
        tool_results(
            tool_call("c1", "delete_everything", {}),
            tool_call("c2", "read_source", {"path": "../outside.md"}),
            tool_call("c3", "read_source", {"path": "notes.md", "max_lines": 999}),
        ),
        final_answer({"findings": [{"statement": "unverified idea", "evidence_digests": []}]}),
    ]
    host, context, envelope, _ = dispatch(tmp_path, monkeypatch, results)

    outcome = search(context, envelope, ResearchArguments())

    assert [call.status for call in outcome.calls] == ["error", "error", "error"]
    assert "unavailable tool" in outcome.calls[0].detail
    assert "in-root" in outcome.calls[1].detail
    assert "max_lines" in outcome.calls[2].detail
    assert outcome.findings[0].information_class is InformationClass.SUBMITTED_CLAIM
    audit = ResearchRecord.model_validate_json(
        host.artifact_store.get_verified(str(outcome.artifacts["audit"]["artifact_id"]), 1)
    )
    assert any("unverified claim: unverified idea" in item for item in audit.unknowns)


def test_empty_search_is_reported_as_empty_not_success(tmp_path, monkeypatch) -> None:
    results = [
        tool_results(tool_call("c1", "search_repository", {"terms": ["zzz_absent_term"]})),
        final_answer({"findings": [{"statement": "no evidence found", "evidence_digests": []}]}),
    ]
    _host, context, envelope, _ = dispatch(tmp_path, monkeypatch, results)

    outcome = search(context, envelope, ResearchArguments())

    assert outcome.calls[0].status == "empty"
    assert outcome.outcome == "completed"
    assert outcome.findings[0].information_class is not InformationClass.VERIFIED_EVIDENCE
    assert "fixture" not in outcome.artifacts


def test_truncation_pending_and_exhausted_are_distinct(tmp_path, monkeypatch) -> None:
    _, truncated_context, truncated_envelope, _ = dispatch(
        tmp_path / "truncated",
        monkeypatch,
        [ProviderResult(content="partial", finish_reason="length")],
    )
    assert search(truncated_context, truncated_envelope, ResearchArguments()).outcome == "truncated"

    loops = [
        tool_results(tool_call(f"p{index}", "search_repository", {"terms": ["checkpoint_cas"]}))
        for index in range(MAX_STEPS)
    ]
    _, pending_context, pending_envelope, _ = dispatch(tmp_path / "pending", monkeypatch, loops)
    pending = search(pending_context, pending_envelope, ResearchArguments())
    assert pending.outcome == "pending"
    assert len(pending.calls) == MAX_STEPS

    over_limit = [
        tool_results(
            *(
                tool_call(f"x{index}", "search_repository", {"terms": ["checkpoint_cas"]})
                for index in range(MAX_TOOL_CALLS + 1)
            )
        )
    ]
    _, exhausted_context, exhausted_envelope, _ = dispatch(tmp_path / "exhausted", monkeypatch, over_limit)
    exhausted = search(exhausted_context, exhausted_envelope, ResearchArguments())
    assert exhausted.outcome == "exhausted"
    assert exhausted.calls == ()


def test_rerun_with_changed_findings_gets_a_new_artifact_identity(tmp_path, monkeypatch) -> None:
    workspace = make_workspace(tmp_path)
    hit = spec_search(workspace, SpecQuery(terms=("checkpoint_cas",))).hits[0]

    def scripted(statement: str) -> list[ProviderResult]:
        return [
            tool_results(tool_call("c1", "search_repository", {"terms": ["checkpoint_cas"]})),
            final_answer({"findings": [{"statement": statement, "evidence_digests": [hit.snippet_digest]}]}),
        ]

    host, context, envelope, _ = dispatch(tmp_path, monkeypatch, scripted("first reading"), workspace=workspace)
    first = search(context, envelope, ResearchArguments())
    monkeypatch.setattr(host, "providers", ScriptedRegistry(ScriptedProvider(scripted("second reading"))))
    second = search(context, envelope, ResearchArguments())

    assert first.artifacts["audit"]["artifact_id"] != second.artifacts["audit"]["artifact_id"]
    assert first.artifacts["audit"]["artifact_digest"] != second.artifacts["audit"]["artifact_digest"]


def test_provider_failure_is_reported_not_hidden(tmp_path, monkeypatch) -> None:
    host, context, envelope, _ = dispatch(tmp_path, monkeypatch, [])
    monkeypatch.setattr(host, "providers", failing_registry())

    outcome = search(context, envelope, ResearchArguments())

    assert outcome.outcome == "failed"
    assert any("provider unavailable" in item for item in outcome.limitations)
    assert "fixture" not in outcome.artifacts
    assert outcome.calls == ()


def test_run_preserves_injected_service_and_rejects_mismatched_root(tmp_path, monkeypatch) -> None:
    host, context, envelope, _ = dispatch(tmp_path, monkeypatch, [])

    class Service:
        def __init__(self, service_host: HostController) -> None:
            self.host = service_host

        def execute_research(self, task_id: str) -> dict[str, object]:
            return {"task": task_id}

    delegated = run(
        SkillContext(host=host, workspace_root=context.workspace_root, research_service=Service(host)),
        envelope,
        ResearchArguments(),
    )
    assert delegated == {"task": TASK_ID}

    other = HostController(tmp_path / "other-state", context.workspace_root)
    with pytest.raises(ValueError, match="different state roots"):
        run(
            SkillContext(host=host, workspace_root=context.workspace_root, research_service=Service(other)),
            envelope,
            ResearchArguments(),
        )
