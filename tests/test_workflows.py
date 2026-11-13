"""Validate the actual role-owned skill definitions and Host stage boundary."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from agent.host.skill_dispatch import role_for_stage
from agent.host.sys_controller import Stage

SKILLS = {
    "auditor": ("audit.yaml", "auditing.py"),
    "researcher": ("research.yaml", "researching.py"),
    "coder": ("code.yaml", "coding.py"),
    "planner": ("plan.yaml", "planning.py"),
    "builder": ("build.yaml", "building.py"),
}


class StrictYamlLoader(yaml.SafeLoader):
    def construct_mapping(self, node, deep=False):
        mapping = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str) or key in mapping:
                raise ValueError("duplicate or invalid YAML key")
            mapping[key] = self.construct_object(value_node, deep=deep)
        return mapping


def load_definition(text: str, *, role: str) -> dict:
    data = yaml.load(text, Loader=StrictYamlLoader)
    if not isinstance(data, dict) or data.get("kind") != "skill_mini_pipeline":
        raise ValueError("invalid skill definition")
    if data.get("owner") != role:
        raise ValueError("skill owner mismatch")
    if data.get("definition_version") != 1:
        raise ValueError("unsupported definition version")
    segments = data.get("segments")
    if not isinstance(segments, list) or not segments:
        raise ValueError("missing segments")
    segment_ids = [segment["id"] for segment in segments]
    if len(set(segment_ids)) != len(segment_ids):
        raise ValueError("duplicate segment")
    for segment in segments:
        steps = segment.get("steps")
        if not isinstance(steps, list) or not steps:
            raise ValueError("empty segment")
        ids = [step["id"] for step in steps]
        if len(set(ids)) != len(ids):
            raise ValueError("duplicate step")
        seen = set()
        for step in steps:
            if not step.get("operation_id"):
                raise ValueError("missing operation identifier")
            if step.get("status") != "unbound":
                raise ValueError("role definition grants unauthorized execution")
            for parent in step.get("depends_on", []):
                if parent not in seen:
                    raise ValueError("missing, forward or recursive dependency")
            seen.add(step["id"])
            ref = step.get("subpipeline_ref")
            if ref:
                prefix, sep, name = ref.partition("#")
                if sep != "#" or prefix != f"agent/skills/{role}/{SKILLS[role][0]}" or name not in segment_ids:
                    raise ValueError("invalid subpipeline reference")
    if data.get("policy", {}).get("can_approve_or_execute") is True:
        raise ValueError("skill cannot self-authorize")
    if data.get("policy", {}).get("issues_approval") is True:
        raise ValueError("skill cannot issue approval")
    return data


def test_role_definitions_are_owned_and_closed() -> None:
    assert not Path("contracts/workflow/pipeline.yaml").exists()
    assert not Path("agent/skills/pipeline_contract.py").exists()
    assert not Path(".agents/contracts/workflow.yaml").exists()
    for role, (yaml_name, implementation) in SKILLS.items():
        root = Path("agent/skills") / role
        assert (root / "SKILL.md").is_file()
        assert (root / implementation).is_file()
        definition = load_definition((root / yaml_name).read_text(encoding="utf-8"), role=role)
        assert definition["pipeline_id"].startswith(role + ".")


def test_host_has_six_stages_but_only_explicit_runtime_skill_routes() -> None:
    assert tuple(s.value for s in Stage) == (
        "research",
        "audit_discovery",
        "planning",
        "fixture_validation",
        "build",
        "build_validation",
    )
    assert role_for_stage("research") == "researcher"
    assert role_for_stage("audit_discovery") == "audit_discovery"
    assert role_for_stage("planning") == "planner"
    assert role_for_stage("build") == "builder"
    for stage in ("fixture_validation", "build_validation", "unknown"):
        with pytest.raises(KeyError):
            role_for_stage(stage)


@pytest.mark.parametrize(
    "mutation", ["duplicate_key", "wrong_owner", "forward_dependency", "unknown_segment", "active_operation"]
)
def test_invalid_role_definitions_block(mutation: str) -> None:
    from copy import deepcopy

    source = (Path("agent/skills/researcher") / "research.yaml").read_text(encoding="utf-8")
    if mutation == "duplicate_key":
        source += "\nowner: researcher\n"
    else:
        definition = yaml.safe_load(source)
        definition = deepcopy(definition)
        if mutation == "wrong_owner":
            definition["owner"] = "builder"
        elif mutation == "forward_dependency":
            definition["segments"][0]["steps"][0]["depends_on"] = ["prepare_retrieval_request"]
        elif mutation == "unknown_segment":
            definition["segments"][2]["steps"][0]["subpipeline_ref"] = "agent/skills/researcher/research.yaml#missing"
        else:
            definition["segments"][0]["steps"][0]["status"] = "active"
        source = yaml.safe_dump(definition)
    with pytest.raises(ValueError):
        load_definition(source, role="researcher")


def test_builder_cannot_issue_approvals_from_yaml() -> None:
    text = (Path("agent/skills/builder") / "build.yaml").read_text(encoding="utf-8")
    data = load_definition(text, role="builder")
    assert data["policy"]["executes_effects"] is False
    assert data["policy"]["issues_approval"] is False
