"""Package and host integration regressions using the actual implementations."""

from importlib.resources import files
from pathlib import Path

import pytest

from agent.skills.auditor.review.core import scan
from agent.skills.builder import building
from agent.skills.coder.coding import review_questions
from agent.skills.planner import planning
from agent.skills.researcher import researching
from system.host.research_catalog import ResearchCatalog
from system.host.skill_dispatch import role_for_stage
from system.host.sys_controller import HostController, Stage, TransitionError
from system.host.sys_policy_enforcer import AuthorizationEngine, AuthorizationError


def test_package_resources_resolve() -> None:
    resource = files("agent.catalog").joinpath("research_samples.yaml")
    assert resource.read_text(encoding="utf-8")
    assert files("agent.skills.researcher").joinpath("research.yaml").read_text(encoding="utf-8")
    assert ResearchCatalog().samples


def test_host_dispatch_has_one_registered_role(tmp_path: Path) -> None:
    host = HostController(tmp_path / "state", tmp_path / "workspace")
    assert host._declared_dispatch_role(Stage.RESEARCH) == "researcher"
    assert host._declared_dispatch_role(Stage.PLANNING) == "planner"
    assert role_for_stage("build") == "builder"
    with pytest.raises(KeyError):
        role_for_stage("unregistered")


def test_path_authorization_remains_default_deny(tmp_path: Path) -> None:
    engine = AuthorizationEngine((str(tmp_path),))
    assert engine.check_path_safety(tmp_path / "file.txt").is_relative_to(tmp_path)
    with pytest.raises(AuthorizationError):
        engine.check_path_safety(tmp_path.parent / "escape.txt")


def test_all_renamed_skills_are_importable() -> None:
    assert callable(scan)
    assert callable(building.run)
    assert callable(review_questions)
    assert callable(planning.run)
    assert callable(researching.run)


def test_mvp_imports_against_new_host() -> None:
    from mvp.api import app
    from mvp.service import MVPService
    assert app is not None
    assert MVPService is not None
