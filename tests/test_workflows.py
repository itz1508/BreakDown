"""Static contract tests for the canonical v6 workflow definition and schemas."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

WORKFLOW_FILE = Path("agents/breakdown.yaml")
PLANS_SCHEMA_FILE = Path("agents/skills/shared/contracts/workflow/processing_plans.schema.json")
REQUIREMENT_SCHEMA_FILE = Path("agents/skills/planner/contracts/requirement_spec.schema.json")

EXPECTED_STAGES = (
    "audit_pre_research",
    "gate_1",
    "research",
    "audit_post_research",
    "planning",
    "builder",
    "completion",
)

EXPECTED_PLAN_OWNERS = {
    "PP1": ("input_processing_plan", "runtime", "auditor", "audit_pre_research"),
    "PP2": ("researcher_processing_plan", "auditor", "researcher", "research"),
    "PP3": ("planner_processing_plan", "auditor", "planner", "planning"),
    "PP4": ("builder_processing_plan", "planner", "builder", "builder"),
}


def load_workflow() -> dict[str, Any]:
    assert WORKFLOW_FILE.is_file(), "agents/breakdown.yaml is the canonical workflow"
    data = yaml.safe_load(WORKFLOW_FILE.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def stages_by_id(workflow: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {stage["id"]: stage for stage in workflow["stages"]}


def object_schemas(node: Any):
    if isinstance(node, dict):
        if node.get("type") == "object":
            yield node
        for value in node.values():
            yield from object_schemas(value)
    elif isinstance(node, list):
        for value in node:
            yield from object_schemas(value)


def criterion_names(node: Any):
    if isinstance(node, dict):
        criterion = node.get("criterion")
        if isinstance(criterion, str):
            yield criterion
        for value in node.values():
            yield from criterion_names(value)
    elif isinstance(node, list):
        for value in node:
            yield from criterion_names(value)


def test_canonical_workflow_is_v6_and_has_seven_stages() -> None:
    workflow = load_workflow()
    stages = workflow["stages"]

    assert workflow["workflow_id"] == "oneshot.breakdown"
    assert workflow["definition_version"] == 6
    assert tuple(stage["id"] for stage in stages) == EXPECTED_STAGES
    assert len({stage["id"] for stage in stages}) == len(stages)
    assert not Path("workflow.yaml").exists()


def test_stage_owners_and_coder_subrole_are_explicit() -> None:
    workflow = load_workflow()
    stages = stages_by_id(workflow)

    assert workflow["ownership"]["user"]["stages"] == ["gate_1"]
    assert workflow["ownership"]["auditor"]["stages"] == [
        "audit_pre_research",
        "audit_post_research",
    ]
    assert workflow["ownership"]["auditor"]["sub_roles"] == ["coder"]
    assert workflow["ownership"]["researcher"]["stages"] == ["research"]
    assert workflow["ownership"]["planner"]["stages"] == ["planning"]
    assert workflow["ownership"]["builder"]["stages"] == ["builder"]
    assert workflow["ownership"]["runtime"]["stages"] == ["completion"]
    assert set(workflow["ownership"]) == {
        "user",
        "auditor",
        "researcher",
        "planner",
        "builder",
        "runtime",
    }
    assert stages["audit_post_research"]["sub_roles"] == ["coder"]


def test_each_stage_has_failure_timeout_and_budget_routes() -> None:
    workflow = load_workflow()
    for stage in workflow["stages"]:
        transitions = stage["transitions"]
        assert {"on_failure", "on_timeout", "on_budget_exhausted"} <= set(transitions)
        for route in transitions.values():
            if isinstance(route, dict):
                assert route.get("next") != "blocked"


def test_four_processing_plans_have_explicit_creation_and_execution_owners() -> None:
    workflow = load_workflow()
    plans = workflow["processing_plans"]["plans"]
    assert set(plans) == set(EXPECTED_PLAN_OWNERS)

    for plan_id, expected in EXPECTED_PLAN_OWNERS.items():
        plan = plans[plan_id]
        assert (
            plan["name"],
            plan["created_by"],
            plan["executed_by"],
            plan["executed_in"],
        ) == expected

    stages = stages_by_id(workflow)
    assert stages["audit_pre_research"]["processing_plan"] == "PP1"
    assert stages["research"]["processing_plan"] == "PP2"
    assert stages["planning"]["processing_plan"] == "PP3"
    assert stages["builder"]["processing_plan"] == "PP4"
    assert stages["audit_pre_research"]["creates_processing_plan"]["id"] == "PP2"
    assert stages["audit_post_research"]["creates_processing_plan"]["id"] == "PP3"
    assert stages["planning"]["substeps"][-1]["creates_processing_plan"]["id"] == "PP4"


def test_gate_is_not_a_plan_input_and_cannot_skip_confirmation() -> None:
    workflow = load_workflow()
    gate = stages_by_id(workflow)["gate_1"]
    research = stages_by_id(workflow)["research"]

    assert gate["owner"] == "user"
    assert gate["decision"]["choices"] == ["confirm", "cancel"]
    assert gate["decision"]["on_confirm"] == "research"
    assert gate["decision"]["on_cancel"] == "completion"
    assert "gate_1_decision" in research["requires"]
    assert "gate_1_decision" not in workflow["processing_plans"]["plans"]["PP2"]


def test_planning_uses_one_canonical_task_list_and_builder_is_sequential() -> None:
    workflow = load_workflow()
    planning = stages_by_id(workflow)["planning"]
    builder = stages_by_id(workflow)["builder"]

    assert workflow["requirement_spec"]["task_list_field"] == "implementation_steps"
    assert "implementation_steps" in workflow["requirement_spec"]["required_fields"]
    assert "builder_processing_steps" not in workflow
    assert "phase_steps" not in workflow
    assert builder["execution_order"] == "sequential"
    assert builder["task_execution"]["canonical_source"] == "requirement_spec.implementation_steps"
    assert builder["task_execution"]["per_task_pattern"] == ["apply", "check", "record"]
    assert builder["task_execution"]["stop_on_first_not_valid"] is True
    assert builder["task_execution"]["per_task_correction_cap"] == 2
    assert builder["task_execution"]["retry"]["max_attempts"] == 1
    assert planning["revision_rules"]["on_preflight_not_valid"]["retry"]["max_attempts"] == 2


def test_builder_correction_cap_is_owned_only_by_builder() -> None:
    workflow = load_workflow()
    for stage in workflow["stages"]:
        if stage["id"] != "builder":
            assert "per_task_correction_cap" not in json.dumps(stage)


def test_obsolete_stages_and_roles_are_absent() -> None:
    workflow = load_workflow()
    stages = stages_by_id(workflow)
    forbidden_stages = {
        "independent_validation",
        "intent_summary",
        "user_review_and_approval",
        "sandbox_execution",
        "completion_and_retention",
        "preflight",
        "build_approval",
    }
    assert not (forbidden_stages & set(stages))
    assert "verifier" not in workflow["ownership"]
    assert "fixturer" not in workflow["ownership"]


def test_artifacts_have_producers_consumers_or_terminal_ownership() -> None:
    workflow = load_workflow()
    produced = {
        artifact
        for stage in workflow["stages"]
        for artifact in stage.get("produces", [])
    }
    consumed = {
        artifact
        for stage in workflow["stages"]
        for artifact in stage.get("requires", []) + stage.get("consumes_when_available", [])
    }
    entry_artifacts = {"user_request", "input_processing_plan", "terminal_outcome"}
    terminal_artifacts = set(workflow["terminal_outputs"])
    assert produced - consumed - terminal_artifacts == set()
    assert consumed - produced - entry_artifacts == set()


def test_requirement_and_processing_plan_schemas_are_closed_objects() -> None:
    requirement = load_json(REQUIREMENT_SCHEMA_FILE)
    plans = load_json(PLANS_SCHEMA_FILE)

    for schema in (requirement, plans):
        objects = list(object_schemas(schema))
        assert objects
        assert all(item.get("additionalProperties") is False for item in objects)

    required = set(requirement["required"])
    assert required == {
        "project_name",
        "overview",
        "technology_stack",
        "prerequisites",
        "core_features",
        "database_schema",
        "api_endpoints_summary",
        "open_questions",
        "implementation_steps",
        "success_criteria",
    }
    record = plans["$defs"]["runtime_plan_record"]
    assert set(record["required"]) == {"plan_id", "status", "criteria_results"}
    assert set(record["properties"]["status"]["enum"]) == {
        "not_run",
        "completed",
        "failed",
        "blocked",
        "skipped",
    }
    assert set(record["properties"]["criteria_results"]["items"]["properties"]["result"]["enum"]) == {
        "valid",
        "not_valid",
        "uncertainty",
    }


def test_result_vocabularies_and_criterion_names_are_unambiguous() -> None:
    workflow = load_workflow()
    names = tuple(criterion_names(workflow))
    for name in names:
        assert not name.endswith(("_passed", "_failed", "_valid", "_not_valid"))
    assert "in_progress" not in json.dumps(workflow)
    plan_rules = set(workflow["processing_plans"]["rules"])
    assert "Processing-plan status values are not_run, completed, failed, blocked and skipped." in plan_rules
    assert "Criteria results use valid, not_valid and uncertainty." in plan_rules
