"""Execute read-only source checks through the host-assigned Auditor role."""

from __future__ import annotations

from dataclasses import dataclass

from agent.audit.core import AuditResult, scan
from agent.contracts.host import HostDispatchEnvelope


@dataclass(frozen=True)
class SkillContext:
    """Skill execution context provided by the host."""

    workspace_root: str


@dataclass(frozen=True)
class AuditArguments:
    """Arguments for the Auditor skill run."""

    scope: str = ""
    capabilities: tuple[str, ...] = ()


def run(context: SkillContext, envelope: HostDispatchEnvelope, arguments: AuditArguments) -> AuditResult:
    """Return source-grounded findings without issuing receipts or modifying source."""
    return scan(
        context.workspace_root,
        scope=arguments.scope,
        capabilities=arguments.capabilities,
        request=envelope.information_needed,
    )
