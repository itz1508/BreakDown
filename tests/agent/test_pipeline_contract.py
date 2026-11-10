"""Read-only Agent mini-pipeline definition regression tests."""

from __future__ import annotations

from pathlib import Path
from shutil import copy2

import pytest
import yaml
from pydantic import ValidationError

from agent.skills.pipeline_contract import DefinitionError, compile_definitions

ROOT = Path(__file__).resolve().parents[2]
YAML_PATHS = (
    "contracts/workflow/pipeline.yaml",
    "agent/skills/auditor/audit.yaml",
    "agent/skills/code_design/code_design.yaml",
    "agent/skills/researcher/research.yaml",
    "agent/skills/planner/plan.yaml",
    "agent/skills/fixturer/Fixture.yaml",
    "agent/skills/builder/build.yaml",
)


@pytest.fixture
def isolated(tmp_path: Path) -> Path:
    refs: set[str] = set()
    for path in YAML_PATHS:
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        copy2(ROOT / path, target)
        refs.update(yaml.safe_load(target.read_text()).get("artifact_contract_refs", []))
    for path in refs:
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.touch()
    (tmp_path / "agent/skills/fixturer/Fixturer.py").touch()
    (tmp_path / "agent/skills/code_design/code_design.py").touch()
    return tmp_path


def update(root: Path, path: str, change) -> None:
    target = root / path
    definition = yaml.safe_load(target.read_text())
    change(definition)
    target.write_text(yaml.safe_dump(definition, sort_keys=False))


def test_valid_graph_inactive(isolated: Path) -> None:
    compiled = compile_definitions(isolated)
    assert len(compiled.root.steps) == 6
    assert tuple(step.id for step in compiled.root.steps) == (
        "auditor_pre", "search_review", "research", "code_design", "planning", "builder_preparation"
    )
    assert len(compiled.role_pipelines) == 6
    assert len(compiled.referenced_operations) == 23
    assert not compiled.activation_ready


def test_registry_check_does_not_activate(isolated: Path) -> None:
    operations = compile_definitions(isolated).referenced_operations
    compiled = compile_definitions(
        isolated, trusted_operation_ids=operations, require_registered=True
    )
    assert compiled.registered_operations == operations
    assert not compiled.activation_ready


def test_unknown_operation_is_rejected(isolated: Path) -> None:
    with pytest.raises(DefinitionError, match="unregistered"):
        compile_definitions(
            isolated, trusted_operation_ids=frozenset(), require_registered=True
        )


def test_root_cycle_is_rejected(isolated: Path) -> None:
    update(isolated, "contracts/workflow/pipeline.yaml", lambda d: d["steps"][0].update(depends_on=["planning"]))
    with pytest.raises(ValidationError, match="cycle"):
        compile_definitions(isolated)


def test_role_cycle_is_rejected(isolated: Path) -> None:
    update(
        isolated, "agent/skills/planner/plan.yaml",
        lambda d: d["segments"][0]["steps"][0].update(depends_on=["return_candidate"]),
    )
    with pytest.raises(ValidationError, match="cycle"):
        compile_definitions(isolated)


def test_duplicate_step_is_rejected(isolated: Path) -> None:
    update(
        isolated, "agent/skills/auditor/audit.yaml",
        lambda d: d["segments"][0]["steps"][1].update(id="inspect_request"),
    )
    with pytest.raises(ValidationError, match="duplicate"):
        compile_definitions(isolated)


def test_unknown_segment_is_rejected(isolated: Path) -> None:
    update(
        isolated, "contracts/workflow/pipeline.yaml",
        lambda d: d["steps"][0].update(
            pipeline_ref="agent/skills/auditor/audit.yaml#wrong"
        ),
    )
    with pytest.raises(DefinitionError, match="unknown pipeline segment"):
        compile_definitions(isolated)


def test_path_traversal_is_rejected(isolated: Path) -> None:
    update(
        isolated, "contracts/workflow/pipeline.yaml",
        lambda d: d["steps"][0].update(
            pipeline_ref="agent/skills/../skills/auditor/audit.yaml#pre"
        ),
    )
    with pytest.raises(DefinitionError, match="disallowed"):
        compile_definitions(isolated)


def test_symlink_ref_is_rejected(isolated: Path) -> None:
    original = isolated / "agent/skills/researcher/research.yaml"
    backup = original.with_name("search_copy.yaml")
    original.rename(backup)
    try:
        original.symlink_to(backup.name)
    except OSError:
        pytest.skip("symlink creation may require additional OS permissions")
    with pytest.raises(DefinitionError, match="symlink"):
        compile_definitions(isolated)


def test_missing_contract_is_rejected(isolated: Path) -> None:
    update(
        isolated, "agent/skills/planner/plan.yaml",
        lambda d: d["artifact_contract_refs"].append(
            "contracts/workflow/planner/missing.py"
        ),
    )
    with pytest.raises(DefinitionError, match="missing"):
        compile_definitions(isolated)


def test_duplicate_yaml_key_is_rejected(isolated: Path) -> None:
    target = isolated / "contracts/workflow/pipeline.yaml"
    target.write_text(target.read_text() + "\nkind: agent_process_graph\n")
    with pytest.raises(DefinitionError, match="duplicate YAML key"):
        compile_definitions(isolated)


def test_subpipeline_recursion_is_rejected(isolated: Path) -> None:
    update(
        isolated, "agent/skills/researcher/research.yaml",
        lambda d: d["segments"][0]["steps"][0].update(
            subpipeline_ref="agent/skills/researcher/research.yaml#main"
        ),
    )
    with pytest.raises(DefinitionError, match="recursive"):
        compile_definitions(isolated)


def test_role_owner_mismatch_is_rejected(isolated: Path) -> None:
    update(
        isolated, "agent/skills/planner/plan.yaml",
        lambda d: d.update(owner="auditor", pipeline_id="auditor.plan"),
    )
    with pytest.raises(DefinitionError, match="owner/path mismatch"):
        compile_definitions(isolated)


def test_yaml_cannot_activate_graph(isolated: Path) -> None:
    update(isolated, "contracts/workflow/pipeline.yaml", lambda d: d.update(activation="active"))
    with pytest.raises(ValidationError, match="activation"):
        compile_definitions(isolated)


def test_canonical_planner_api_is_fail_closed() -> None:
    from importlib.util import find_spec

    from agent.skills.planner import planning

    assert find_spec("agent.skills.planner.plan") is None
    assert find_spec("agent.skills.planner.planning") is not None
    with pytest.raises(planning.PlanningPipelineNotActive, match="executor is required"):
        planning.create(object(), object())
    with pytest.raises(ValueError, match="requires"):
        planning.create(None, object())
