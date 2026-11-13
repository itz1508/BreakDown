"""Sandbox-local bounded traceback normalization (no source reads or instrumentation)."""

from __future__ import annotations

import re
import traceback
from pathlib import Path

from agent.host.contracts.system.diagnostic import FrameEvidence, NormalizedException

_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]{0,95}\Z")
_MODULE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*\Z")
_MAX_FRAMES = 12
_MAX_CHAIN = 4


def _safe_name(value: object, *, dotted: bool = False) -> str:
    if (
        isinstance(value, str)
        and len(value) <= (160 if dotted else 96)
        and (_MODULE if dotted else _IDENTIFIER).fullmatch(value)
    ):
        return value
    return "unknown"


def _safe_location(filename: str, source_root: Path | None) -> str:
    """Never disclose absolute filesystem paths or traceframes outside the root."""
    if source_root is None:
        return "<source-unbound>"
    try:
        root = Path(source_root).resolve(strict=False)
        relative = Path(filename).resolve(strict=False).relative_to(root)
        normalized = relative.as_posix()
        if not normalized or len(normalized) > 240:
            return "<path-redacted>"
        if any(ord(ch) < 32 or 0xD800 <= ord(ch) <= 0xDFFF for ch in normalized):
            return "<path-redacted>"
        return normalized
    except (ValueError, OSError, RuntimeError, UnicodeError):
        return "<outside-root>"


def normalize_exception(
    error: BaseException,
    *,
    source_root: Path | None = None,
    max_frames: int = _MAX_FRAMES,
    max_chain: int = _MAX_CHAIN,
) -> NormalizedException:
    """Convert an exception into bounded, non-sensitive diagnostic metadata.

    No error messages, source lines, locals, absolute paths or repr(error) survive.
    Frame positions and chained exception types are retained for diagnosis.
    """
    if not isinstance(error, BaseException):
        raise TypeError("error must be a BaseException")
    if not 1 <= max_frames <= _MAX_FRAMES or not 0 <= max_chain <= _MAX_CHAIN:
        raise ValueError("invalid traceback limits")
    # extract_tb reads stack metadata only; never retrieve locals or lines.
    frames = traceback.StackSummary.extract(traceback.walk_tb(error.__traceback__), limit=None, lookup_lines=False)
    selected = frames[-max_frames:]
    normalized_frames = tuple(
        FrameEvidence(
            path=_safe_location(frame.filename, source_root),
            line=max(1, frame.lineno or 1),
            function=_safe_name(frame.name),
        )
        for frame in selected
    )
    chains: list[str] = []
    seen = {id(error)}
    current: BaseException = error
    while len(chains) < max_chain:
        chained = current.__cause__ or (current.__context__ if not current.__suppress_context__ else None)
        if chained is None or id(chained) in seen:
            break
        seen.add(id(chained))
        chains.append(_safe_name(type(chained).__name__))
        current = chained
    next_exc = current.__cause__ or (current.__context__ if not current.__suppress_context__ else None)
    name = getattr(error, "name", None) if isinstance(error, (ImportError, NameError)) else None
    module_name = _safe_name(name, dotted=True) if name is not None else None
    return NormalizedException(
        type=_safe_name(type(error).__name__),
        module_name=module_name,
        frames=normalized_frames,
        cause_types=tuple(chains),
        frames_truncated=len(frames) > max_frames,
        chain_truncated=next_exc is not None and id(next_exc) not in seen,
    )
