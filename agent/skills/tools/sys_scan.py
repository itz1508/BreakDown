"""Passive runtime capability observation; never installs monitoring hooks."""

from __future__ import annotations

import sys
from collections.abc import Iterable
from itertools import islice


def sys_scan(fields: Iterable[str] = ("monitoring_available",)) -> dict[str, bool]:
    """Return only requested, supported interpreter capabilities.

    ``sys.monitoring`` exists on CPython 3.12+, but checking its presence
    does not reserve tool IDs, enable events, or authorize instrumentation.
    """
    if isinstance(fields, (str, bytes)):
        raise ValueError("fields must be a collection")
    requested = tuple(islice(fields, 2))
    if len(requested) > 1 or requested not in ((), ("monitoring_available",)):
        raise ValueError("only monitoring_available is supported")
    return {"monitoring_available": hasattr(sys, "monitoring")} if requested else {}
