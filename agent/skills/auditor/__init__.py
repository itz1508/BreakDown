"""Auditor skill — read-only repository inspection, CodeIntent, source-grounded findings.

Ownership:
    Read-only repository inspection, CodeIntent discovery, source-grounded
    diagnostic findings. The Auditor never mutates state, never issues
    receipts, and never authorizes operations. All findings are candidate
    observations that the Runtime host evaluates and acts upon.

Tools:
    paths — filesystem integrity, broken symlinks, repo containment
    security — security-sensitive source pattern detection
    state — static host ownership and receipt-binding audits

Runtime integration:
    Findings are reported through the HostDispatchResult envelope. The
    Runtime validates, persists, and acts on Auditor output.
"""

from agent.skills.auditor.run import post_dispatch, pre_dispatch

__all__ = ["post_dispatch", "pre_dispatch"]
