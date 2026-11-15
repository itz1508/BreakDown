"""Focused probe for the repaired agents CheckpointStore, observability model, and primitive identity."""

from __future__ import annotations

import shutil
from pathlib import Path

state = Path(".audit-0f842dc/probe_state")
shutil.rmtree(state, ignore_errors=True)

from agents.skills.shared.storage.checkpoint_store import CheckpointStore  # noqa: E402

store = CheckpointStore(state)
rev, digest = store.checkpoint_cas("task-1", 0, {"stage": "probe"})
loaded = store.load_checkpoint("task-1")
assert loaded is not None, "load_checkpoint returned None"
assert loaded[0] == rev and loaded[1] == {"stage": "probe"}, loaded
op = store.record_operation("task-1", rev, "create", "probe.py")
store.update_operation_status(op, "completed")
print(f"P1 probe OK: rev={rev} loaded_state={loaded[1]} op={op} digest={digest[:12]}...")

from agents.skills.shared.contracts.workflow.system import observability  # noqa: E402

trace = observability.TraceContext(trace_id="trace-1", metadata={"k": "v"})
restored = observability.TraceContext.model_validate_json(trace.model_dump_json())
assert restored == trace
print(f"P2 probe OK: TraceContext round-trip trace_id={restored.trace_id}")

from contracts.workflow.common import DiagnosticStatus as DCommon  # noqa: E402
from contracts.workflow.shared import Sha256 as SShared  # noqa: E402

from agents.shared.base import DiagnosticStatus, Sha256  # noqa: E402

assert DiagnosticStatus is DCommon, "contracts.workflow.common identity broken"
assert Sha256 is SShared, "contracts.workflow.shared identity broken"
print("P7-adjacent probe OK: primitive identity unified across legacy shims")

shutil.rmtree(state, ignore_errors=True)
print("ALL PROBES PASSED")
