"""System layer: infrastructure independent of the agents package.

Runtime facade: coordination, delegation, references, process I/O and storage.
The stdin/stdout JSON envelope (Request/Response) lives in ``system._runtime``.
"""

from __future__ import annotations

from system._call import UnknownSkillActionError, call_ref
from system._coordinate import coordinate
from system._delegating import delegating
from system._runtime import (
    Request,
    Response,
    RuntimeResult,
    error_response,
    ok_response,
    read_request,
    sys_runtime,
    write_response,
)
from system.storage import Storage, sys_ref, sys_storage

__all__ = [
    "Request",
    "Response",
    "RuntimeResult",
    "Storage",
    "UnknownSkillActionError",
    "call_ref",
    "coordinate",
    "delegating",
    "error_response",
    "ok_response",
    "read_request",
    "sys_ref",
    "sys_runtime",
    "sys_storage",
    "write_response",
]
