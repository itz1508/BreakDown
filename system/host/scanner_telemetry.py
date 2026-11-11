"""Optional, single-backend telemetry for Host-owned Scanner operations.

Telemetry is never an evidence authority. ArtifactStore and receipts remain
canonical. Only stable run identifiers are emitted: no prompts, source,
tracebacks, secrets, model outputs, or arbitrary exception messages.

Logfire is preferred when available, without needing a hosted API key for local
instrumentation. OpenTelemetry uses the application's existing tracer provider
as a fallback; it never installs a second provider or exporter here.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Iterator
from contextlib import AbstractContextManager, contextmanager, suppress
from typing import Literal

Backend = Literal["disabled", "logfire", "opentelemetry"]
_attempted = False
_backend: Backend = "disabled"


def configure_logfire() -> None:
    """Initialize once at trusted Host startup; preserve legacy entry point.

    ONESHOT_LOGFIRE_ENABLED=1 enables local instrumentation.
    With no LOGFIRE_TOKEN, hosted Logfire export is explicitly disabled—even
    when cached credentials or LOGFIRE_API_KEY might otherwise be discovered.
    A LOGFIRE_TOKEN explicitly enables hosted export. Any separately configured
    OTLP exporter still obeys its own endpoint/authentication settings.
    """
    global _attempted, _backend
    if _attempted:
        return
    _attempted = True
    if os.environ.get("ONESHOT_LOGFIRE_ENABLED") != "1":
        return
    try:
        import logfire

        logfire.configure(
            send_to_logfire="if-token-present" if os.environ.get("LOGFIRE_TOKEN") else False,
            console=False,
            service_name="breakdown-scanner",
        )
    except Exception:  # Fail open for optional telemetry only.
        pass
    else:
        _backend = "logfire"
        return
    try:
        from opentelemetry import trace

        # Reuse the Host's installed provider. No global TracerProvider, exporter,
        # auto-instrumentation, or OTLP destination is created here.
        trace.get_tracer("breakdown.scanner")
    except Exception:
        _backend = "disabled"
    else:
        _backend = "opentelemetry"


def telemetry_backend() -> Backend:
    """Selected instrumentation API; does not imply successful export."""
    return _backend


@contextmanager
def scanner_span(task_id: str, run_id: str, artifact_id: str) -> Iterator[None]:
    """One bounded metadata-only span; exporter failures cannot replace work."""
    if _backend == "disabled":
        yield
        return
    try:
        span: AbstractContextManager[object]
        if _backend == "logfire":
            import logfire

            span = logfire.span(
                "scanner.run", task_id=task_id, run_id=run_id, artifact_id=artifact_id
            )
        else:
            from opentelemetry import trace

            span = trace.get_tracer("breakdown.scanner").start_as_current_span(
                "scanner.run",
                attributes={
                    "task_id": task_id,
                    "run_id": run_id,
                    "artifact_id": artifact_id,
                },
                record_exception=False,
                set_status_on_exception=False,
            )
        span.__enter__()
    except Exception:
        yield
        return
    try:
        yield
    finally:
        # An exporter error must never hide the original scanner exception.
        with suppress(Exception):
            span.__exit__(*sys.exc_info())
