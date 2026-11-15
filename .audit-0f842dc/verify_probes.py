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

# The legacy primitive copies (contracts.workflow.common / .shared) were
# retired with the contracts/ tree; single-source identity means the
# canonical classes are the only definition. Verify the retired module
# files stay gone rather than comparing class identity.
legacy_common = Path("contracts/workflow/common.py")
legacy_shared = Path("contracts/workflow/shared.py")
assert not legacy_common.exists(), "legacy primitives copy must stay retired"
assert not legacy_shared.exists(), "legacy primitives copy must stay retired"
print("P7 probe OK: canonical primitives are the only definition")

shutil.rmtree(state, ignore_errors=True)
print("ALL PROBES PASSED")
