"""Execute read-only source checks through the host-assigned Auditor role."""

from __future__ import annotations

from agent.skills.auditor.review.core import AuditResult, scan
from contracts.workflow.system.host import HostDispatchEnvelope
from system.host.skill_dispatch import AuditArguments, SkillContext


def run(context: SkillContext, envelope: HostDispatchEnvelope, arguments: AuditArguments) -> AuditResult:
    """Return source-grounded findings without issuing receipts or modifying source."""
    return scan(
        context.workspace_root,
        scope=arguments.scope,
        capabilities=arguments.capabilities,
        request=envelope.information_needed,
    )
