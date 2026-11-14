"""Host-controlled dispatch for executable role skills.

Validates the persisted task/run/stage/role/return route before any skill loads.
Only Runtime may grant authority and persist trusted evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Protocol, TypeAlias

from agents.skills.builder.contracts.schedule import BuildWave
from agents.skills.builder.effect_executor import EffectExecutor
from agents.skills.planner.contracts.scanner import ScannerRunInput
from agents.skills.shared.contracts.workflow.system.host import BuildAdmissionReceipt, HostDispatchEnvelope
from agents.skills.shared.host.sys_controller import HostController, TransitionError


class ResearchExecutionService(Protocol):
    """Host-provided executor; no service implementation is inferred."""

    @property
    def host(self) -> HostController: ...

    def execute_research(self, task_id: str) -> dict[str, object]: ...


_ROLE_MODULES = {
    ("discovery", "auditor"): "agents.skills.auditor.auditing",
    ("research", "researcher"): "agents.skills.researcher.researching",
    ("repository_reconciliation", "auditor"): "agents.skills.auditor.auditing",
    ("candidate_completion", "coder"): "agents.skills.coder.coding",
    ("gap_inspection", "auditor"): "agents.skills.auditor.auditing",
    ("planning", "planner"): "agents.skills.planner.planning",
    ("sandbox_execution", "builder"): "agents.skills.builder.building",
}


def role_for_stage(stage: str) -> str:
    """Return exactly one registered executable role for a Host stage."""
    matches = [role for registered_stage, role in _ROLE_MODULES if registered_stage == stage]
    if len(matches) != 1:
        raise KeyError(stage)
    return matches[0]


@dataclass(frozen=True)
class AuditArguments:
    scope: str = "."
    capabilities: tuple[str, ...] = ()


@dataclass(frozen=True)
class ResearchArguments:
    """Execute only an existing Research task."""


@dataclass(frozen=True)
class PlanningArguments:
    scan: ScannerRunInput


@dataclass(frozen=True)
class BuildArguments:
    action_id: str
    action_kind: str
    admission_receipt: BuildAdmissionReceipt
    target_path: str | None = None
    source_path: str | None = None
    content: str | None = None
    expected_source_digest: str | None = None
    wave: BuildWave | None = None


RoleArguments: TypeAlias = AuditArguments | ResearchArguments | PlanningArguments | BuildArguments


@dataclass(frozen=True)
class SkillContext:
    """Dependencies provisioned exclusively by HostController."""

    host: HostController
    workspace_root: Path
    research_service: ResearchExecutionService | None = None

    @classmethod
    def from_host(
        cls,
        host: HostController,
        workspace_root: str | Path,
        research_service: ResearchExecutionService | None = None,
    ) -> SkillContext:
        root = Path(workspace_root).resolve(strict=True)
        if not root.is_dir():
            raise ValueError("workspace must be a directory")
        host.authorization.check_path_safety(root)
        return cls(host=host, workspace_root=root, research_service=research_service)

    def build_executor(self) -> EffectExecutor:
        """Return the already-authorized Runtime effect executor."""
        return EffectExecutor(
            authorization=self.host.authorization,
            checkpoint_store=self.host.checkpoint_store,
            receipt_store=self.host.receipt_store,
            workspace_root=self.workspace_root,
            artifact_store=self.host.artifact_store,
        )


SkillOutput: TypeAlias = object


def execute_skill(context: SkillContext, envelope: HostDispatchEnvelope, arguments: RoleArguments) -> SkillOutput:
    """Fail closed on mismatched routing, arguments, or missing role registrations."""
    context.host.verify_agent_dispatch(envelope)
    key = (envelope.stage, envelope.role)
    module_name = _ROLE_MODULES.get(key)
    expected_type = {
        ("discovery", "auditor"): AuditArguments,
        ("research", "researcher"): ResearchArguments,
        ("repository_reconciliation", "auditor"): AuditArguments,
        ("candidate_completion", "coder"): AuditArguments,
        ("gap_inspection", "auditor"): AuditArguments,
        ("planning", "planner"): PlanningArguments,
        ("sandbox_execution", "builder"): BuildArguments,
    }.get(key)
    if module_name is None or expected_type is None:
        raise TransitionError("no executable skill registered for this stage and role")
    if type(arguments) is not expected_type:
        raise TransitionError("skill argument type does not match the verified stage and role")
    context.host.event_store.append(envelope.task_id, "skill_started", f"{envelope.stage}:{envelope.role}")
    try:
        outcome = import_module(module_name).run(context, envelope, arguments)
    except Exception:
        context.host.event_store.append(envelope.task_id, "skill_failed", f"{envelope.stage}:{envelope.role}")
        raise
    context.host.event_store.append(envelope.task_id, "skill_finished", f"{envelope.stage}:{envelope.role}")
    return outcome


def registered_skills() -> list[dict[str, str]]:
    """List only the four installed skill entrypoints."""
    return [
        {"stage": stage, "contract_role": role, "module": module}
        for (stage, role), module in sorted(_ROLE_MODULES.items())
    ]
