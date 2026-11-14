"""Tests for the single workflow definition and its two user approval stops."""

from pathlib import Path

import yaml

WORKFLOW_FILE = Path("workflow.yaml")

EXPECTED_STAGES = (
    "user_request",
    "intent_summary",
    "search_confirmation",
    "catalog_discovery",
    "discovery",
    "research",
    "repository_audit",
    "planning",
    "build_approval",
    "builder",
    "preflight",
    "sandbox_execution",
    "independent_validation",
    "completion_and_retention",
)


def load_workflow() -> dict:
    assert WORKFLOW_FILE.is_file(), "workflow.yaml must exist at the repository root"
    data = yaml.safe_load(WORKFLOW_FILE.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def stages_by_id(workflow: dict) -> dict[str, dict]:
    stages = workflow["stages"]
    return {stage["id"]: stage for stage in stages}


def test_workflow_has_one_ordered_definition() -> None:
    workflow = load_workflow()
    stages = workflow["stages"]

    assert workflow["workflow_id"] == "oneshot.breakdown"
    assert workflow["definition_version"] == 3
    assert tuple(stage["id"] for stage in stages) == EXPECTED_STAGES
    assert [stage["order"] for stage in stages] == list(range(1, len(EXPECTED_STAGES) + 1))
    assert len({stage["id"] for stage in stages}) == len(stages)


def test_workflow_has_exactly_two_user_approval_stops() -> None:
    workflow = load_workflow()
    approval_stages = [
        stage["id"]
        for stage in workflow["stages"]
        if stage.get("approval", {}).get("required") is True
    ]

    assert approval_stages == ["search_confirmation", "build_approval"]
    assert stages_by_id(workflow)["search_confirmation"]["owner"] == "user"
    assert stages_by_id(workflow)["build_approval"]["owner"] == "user"


def test_search_approval_happens_before_catalog_repository_or_external_search() -> None:
    workflow = load_workflow()
    stages = stages_by_id(workflow)
    gate = stages["search_confirmation"]
    catalog = stages["catalog_discovery"]
    discovery = stages["discovery"]
    research = stages["research"]

    assert gate["approval"]["binds_to"] == ["intent_summary", "search_scope"]
    assert gate["approval"]["on_approved"] == "catalog_discovery"
    assert gate["approval"]["on_changes_requested"] == "intent_summary"
    assert gate["approval"]["on_declined"] == "stop_before_search"
    assert {"search_approval", "approved_search_scope"} <= set(catalog["requires"])
    assert "search_approval" in discovery["requires"]
    assert "search_approval" in research["requires"]
    assert gate["order"] < min(catalog["order"], discovery["order"], research["order"])


def test_build_approval_binds_the_exact_plan_and_source() -> None:
    workflow = load_workflow()
    stages = stages_by_id(workflow)
    gate = stages["build_approval"]
    required_bindings = {
        "plan_revision",
        "plan_package_digest",
        "assessed_source_checkpoint",
    }

    assert required_bindings <= set(gate["approval"]["binds_to"])
    assert gate["approval"]["on_approved"] == "builder"
    assert gate["approval"]["on_changes_requested"] == "planning"
    assert gate["approval"]["on_declined"] == "stop_before_build"
    assert "user_approval" in stages["builder"]["requires"]
    assert "user_approval" in stages["preflight"]["requires"]
    assert "user_approval" in stages["sandbox_execution"]["requires"]


def test_builder_owns_build_setup_and_execution() -> None:
    workflow = load_workflow()
    stages = stages_by_id(workflow)
    ownership = workflow["ownership"]["builder"]

    assert ownership["stages"] == ["builder", "preflight", "sandbox_execution"]
    assert {
        "build_contract",
        "build_entry_point",
        "build_implementation",
        "sandbox_creation",
        "approved_source_changes",
        "build_execution",
    } <= set(ownership["owns"])
    assert all(stages[name]["owner"] == "builder" for name in ownership["stages"])
    assert stages["sandbox_execution"]["execution_condition"]["preflight_result"] == "ready"


def test_auditor_owns_both_audit_stages_and_its_three_files() -> None:
    workflow = load_workflow()
    stages = stages_by_id(workflow)
    auditor = workflow["skill_scaffolding"]["auditor"]

    assert workflow["ownership"]["auditor"]["stages"] == ["discovery", "repository_audit"]
    assert auditor == {
        "directory": "agent/skills/auditor/",
        "contract_file": "audit.yaml",
        "entry_file": "audit.py",
        "implementation_file": "auditing.py",
    }
    assert stages["discovery"]["owner"] == "auditor"
    assert stages["repository_audit"]["owner"] == "auditor"
    assert workflow["ownership"]["auditor"]["application_source_changes"] is False


def test_each_skill_keeps_its_three_files_inside_its_own_folder() -> None:
    workflow = load_workflow()
    expected = {
        "auditor": ("audit.yaml", "audit.py", "auditing.py"),
        "researcher": ("research.yaml", "research.py", "researching.py"),
        "planner": ("plan.yaml", "plan.py", "planning.py"),
        "builder": ("build.yaml", "build.py", "building.py"),
        "verifier": ("verify.yaml", "verify.py", "verifying.py"),
    }

    assert set(workflow["skill_scaffolding"]) == set(expected)
    for role, names in expected.items():
        scaffold = workflow["skill_scaffolding"][role]
        assert scaffold["directory"] == f"agent/skills/{role}/"
        assert (
            scaffold["contract_file"],
            scaffold["entry_file"],
            scaffold["implementation_file"],
        ) == names
        assert "contracts/" not in scaffold["directory"]
        assert "host/" not in scaffold["directory"]


def test_catalog_is_a_reference_source_not_an_approval_authority() -> None:
    workflow = load_workflow()
    catalog = stages_by_id(workflow)["catalog_discovery"]

    assert catalog["owner"] == "workflow"
    assert "search_approval" in catalog["requires"]
    assert "Catalog entries are references, not proof." in catalog["rules"]
    assert "Catalog entries do not create requirements." in catalog["rules"]
    assert "Catalog results do not approve research or build work." in catalog["rules"]


def test_validation_is_independent_from_builder() -> None:
    workflow = load_workflow()
    stages = stages_by_id(workflow)

    assert stages["independent_validation"]["owner"] == "verifier"
    assert workflow["ownership"]["verifier"]["independence_required"] is True
    assert stages["independent_validation"]["outcomes"]["valid"]["next"] == "completion_and_retention"
    assert stages["independent_validation"]["outcomes"]["not_valid"]["next"] == "planning"
    assert stages["completion_and_retention"]["completion_condition"]["validation_result"] == "valid"


def test_workflow_stages_do_not_contain_skill_implementation_details() -> None:
    workflow = load_workflow()
    forbidden_stage_fields = {
        "module",
        "entry",
        "contract",
        "skill",
        "runtime",
        "behavior",
    }

    for stage in workflow["stages"]:
        assert not (forbidden_stage_fields & set(stage)), stage["id"]
        assert stage["owner"] != "host"
