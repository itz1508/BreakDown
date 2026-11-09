"""Upscale via belt Topaz."""

from __future__ import annotations

import json
import subprocess
from typing import Any


def run_upscale(video_url: str, model: str = "falai/topaz-video-upscaler") -> dict[str, Any]:
    payload = {"video_url": video_url}
    cmd = ["belt", "app", "run", model, "--input", json.dumps(payload)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600, check=False)
    except FileNotFoundError:
        return {"status": "blocked", "reason": "belt CLI not installed", "model": model}
    if result.returncode != 0:
        return {"status": "error", "stderr": result.stderr.strip(), "model": model}
    try:
        data = json.loads(result.stdout) if result.stdout.strip().startswith("{") else {"raw": result.stdout}
    except json.JSONDecodeError:
        data = {"raw": result.stdout}
    return {"status": "completed", "model": model, "payload": payload, "result": data}
