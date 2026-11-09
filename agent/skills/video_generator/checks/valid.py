"""Checks for prompt → video validity."""

from __future__ import annotations


def check_prompt_valid(prompt: str) -> bool:
    return isinstance(prompt, str) and 1 <= len(prompt.strip()) <= 5000


def check_duration_valid(duration: int | None, model: str) -> bool:
    if duration is None:
        return True
    max_by_model = {
        "alibaba/happyhorse-1-0-t2v": 15,
        "bytedance/seedance-2-0": 10,
        "xai/grok-imagine-video": 10,
    }
    limit = max_by_model.get(model, 10)
    return 1 <= duration <= limit


def check_resolution_valid(resolution: str | None) -> bool:
    if resolution is None:
        return True
    return resolution in ("480P", "720P", "1080P", "1080p")


__all__ = ["check_duration_valid", "check_prompt_valid", "check_resolution_valid"]
