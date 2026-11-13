"""Isolated regression tests for the existing Host scanner telemetry API."""

import importlib.util
import sys
import types
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parents[1] / "agent" / "skills" / "planner" / "scanner_telemetry.py"


def load(monkeypatch, *, logfire=None, logfire_error=False, otel=None, enabled=True, token=None):
    monkeypatch.setenv("ONESHOT_LOGFIRE_ENABLED", "1" if enabled else "0")
    monkeypatch.delenv("LOGFIRE_TOKEN", raising=False)
    if token:
        monkeypatch.setenv("LOGFIRE_TOKEN", token)
    if logfire is not None:
        monkeypatch.setitem(sys.modules, "logfire", logfire)
    elif logfire_error:
        monkeypatch.setitem(sys.modules, "logfire", None)
    if otel is not None:
        monkeypatch.setitem(sys.modules, "opentelemetry", otel)
    spec = importlib.util.spec_from_file_location("isolated_scanner_telemetry", SOURCE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.configure_logfire()
    return mod


class Span:
    def __init__(self, calls, fail_exit=False):
        self.calls = calls
        self.fail_exit = fail_exit

    def __enter__(self):
        self.calls.append("enter")
        return self

    def __exit__(self, *args):
        self.calls.append("exit")
        if self.fail_exit:
            raise RuntimeError("exporter failure")


def make_logfire(calls, *, fail_exit=False):
    m = types.ModuleType("logfire")
    m.configure = lambda **kwargs: calls.append(("configure", kwargs))

    def span(name, **attrs):
        calls.append(("span", name, attrs))
        return Span(calls, fail_exit=fail_exit)

    m.span = span
    return m


def make_otel(calls):
    trace = types.ModuleType("opentelemetry.trace")

    class Tracer:
        def start_as_current_span(self, name, **kwargs):
            calls.append(("otel.span", name, kwargs))
            return Span(calls)

    trace.get_tracer = lambda *args: Tracer()
    otel = types.ModuleType("opentelemetry")
    otel.trace = trace
    return otel


def test_no_key_local_logfire_never_attempts_hosted_export(monkeypatch):
    calls = []
    mod = load(monkeypatch, logfire=make_logfire(calls))
    assert mod.telemetry_backend() == "logfire"
    assert calls == [("configure", {"send_to_logfire": False, "console": False, "service_name": "breakdown-scanner"})]
    with mod.scanner_span("t", "r", "a"):
        pass
    assert ("span", "scanner.run", {"task_id": "t", "run_id": "r", "artifact_id": "a"}) in calls
    assert calls.count("enter") == calls.count("exit") == 1


def test_explicit_write_token_enables_optional_hosted_logfire(monkeypatch):
    calls = []
    mod = load(monkeypatch, logfire=make_logfire(calls), token="test-token")
    assert mod.telemetry_backend() == "logfire"
    assert calls[0][1]["send_to_logfire"] == "if-token-present"
    assert "token" not in calls[0][1]
    assert "api_key" not in calls[0][1]


def test_fallback_to_existing_opentelemetry_without_new_exporter(monkeypatch):
    calls = []
    mod = load(monkeypatch, logfire_error=True, otel=make_otel(calls))
    assert mod.telemetry_backend() == "opentelemetry"
    with mod.scanner_span("task-1", "run-1", "art-1"):
        pass
    assert calls[0] == (
        "otel.span",
        "scanner.run",
        {
            "attributes": {"task_id": "task-1", "run_id": "run-1", "artifact_id": "art-1"},
            "record_exception": False,
            "set_status_on_exception": False,
        },
    )
    assert calls[-2:] == ["enter", "exit"]


def test_disabled_never_emits_spans(monkeypatch):
    calls = []
    mod = load(monkeypatch, logfire=make_logfire(calls), enabled=False)
    assert mod.telemetry_backend() == "disabled"
    with mod.scanner_span("x", "y", "z"):
        pass
    assert not calls


def test_exporter_exit_failure_never_masks_work(monkeypatch):
    calls = []
    mod = load(monkeypatch, logfire=make_logfire(calls, fail_exit=True))
    with pytest.raises(ValueError, match="real scanner failure"), mod.scanner_span("x", "y", "z"):
        raise ValueError("real scanner failure")
    assert calls[-1] == "exit"


def test_repeated_setup_is_idempotent(monkeypatch):
    calls = []
    mod = load(monkeypatch, logfire=make_logfire(calls))
    mod.configure_logfire()
    assert len(calls) == 1


def test_no_configured_backend_is_nonfatal(monkeypatch):
    monkeypatch.setitem(sys.modules, "logfire", None)
    monkeypatch.setitem(sys.modules, "opentelemetry", None)
    mod = load(monkeypatch, enabled=True)
    assert mod.telemetry_backend() == "disabled"
    with mod.scanner_span("t", "r", "a"):
        pass


def test_real_opentelemetry_sdk_emits_single_metadata_only_span(monkeypatch):
    # SDK test proves actual local tracing without any Logfire API key.
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

    provider = TracerProvider()
    exporter = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    mod = load(monkeypatch, logfire_error=True)
    assert mod.telemetry_backend() == "opentelemetry"
    with mod.scanner_span("task", "run", "artifact"):
        pass
    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    span = spans[0]
    assert span.name == "scanner.run"
    assert dict(span.attributes) == {"task_id": "task", "run_id": "run", "artifact_id": "artifact"}
    assert not span.events
    provider.shutdown()


def test_logfire_configuration_error_uses_otel_fallback(monkeypatch):
    calls = []
    fake = make_logfire(calls)

    def broken(**kwargs):
        raise RuntimeError("unavailable backend")

    fake.configure = broken
    mod = load(monkeypatch, logfire=fake, otel=make_otel(calls))
    assert mod.telemetry_backend() == "opentelemetry"
    with mod.scanner_span("t", "r", "a"):
        pass
    assert any(isinstance(call, tuple) and call[0] == "otel.span" for call in calls)


def test_logfire_api_key_alone_does_not_authorize_export(monkeypatch):
    calls = []
    monkeypatch.setenv("LOGFIRE_API_KEY", "test-remote-key")
    mod = load(monkeypatch, logfire=make_logfire(calls))
    assert mod.telemetry_backend() == "logfire"
    assert calls[0][1]["send_to_logfire"] is False


def test_otel_does_not_capture_failure_message(monkeypatch):
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

    provider = TracerProvider()
    exporter = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    # Run with an already-installed provider where supported; the SDK warns
    # rather than replacing it, so isolate this case by overriding get_tracer.
    tracer = provider.get_tracer("breakdown.scanner")
    monkeypatch.setattr(trace, "get_tracer", lambda name: tracer)
    mod = load(monkeypatch, logfire_error=True)
    with pytest.raises(RuntimeError, match="TOP SECRET VALUE"), mod.scanner_span("t", "r", "a"):
        raise RuntimeError("TOP SECRET VALUE")
    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    assert not spans[0].events
    assert not any("TOP SECRET" in str(v) for v in spans[0].attributes.values())
    provider.shutdown()
