"""Text-to-video via belt."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


def run_generate(
    prompt: str,
    model: str = "google/veo-3-1-fast",
    duration: int | None = None,
    resolution: str | None = None,
    generate_audio: bool | None = None,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """Execute text-to-video via belt.

    Args:
        prompt: Text prompt for generation.
        model: belt app ID (e.g., google/veo-3-1-fast, bytedance/seedance-2-0).
        duration: seconds (model-dependent).
        resolution: e.g., 1080P, 720P.
        generate_audio: Seedance audio flag.

    Returns:
        dict with belt stdout evidence and requested model.
    """
    payload: dict[str, Any] = {"prompt": prompt}
    if duration is not None:
        payload["duration"] = duration
    if resolution is not None:
        payload["resolution"] = resolution
    if generate_audio is not None:
        payload["generate_audio"] = generate_audio

    cmd = ["belt", "app", "run", model, "--input", json.dumps(payload)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600, check=False)
    except FileNotFoundError:
        return {"status": "blocked", "reason": "belt CLI not installed", "model": model, "prompt": prompt}
    if result.returncode != 0:
        return {"status": "error", "stderr": result.stderr.strip(), "model": model}
    # belt returns JSON with video_url / job_id
    try:
        data = json.loads(result.stdout) if result.stdout.strip().startswith("{") else {"raw": result.stdout}
    except json.JSONDecodeError:
        data = {"raw": result.stdout}
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
    return {"status": "completed", "model": model, "payload": payload, "result": data}
