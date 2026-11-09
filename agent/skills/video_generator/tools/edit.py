"""Video editing via belt."""

from __future__ import annotations

import json
import subprocess
from typing import Any


def run_edit(video: str, prompt: str, model: str = "alibaba/happyhorse-1-0-video-edit") -> dict[str, Any]:
    payload = {"video": video, "prompt": prompt}
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
