"""Image-to-video via belt."""

from __future__ import annotations

import json
import subprocess
from typing import Any


def run_image_to_video(
    image_url: str,
    prompt: str | None = None,
    model: str = "falai/wan-2-5",
    reference_image: str | None = None,
    generate_audio: bool | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"image_url": image_url}
    # Adapt keys per model: Seedance uses `image`, HappyHorse uses `image_url`
    if "seedance" in model and "image" not in payload:
        payload["image"] = payload.pop("image_url")
    if prompt:
        payload["prompt"] = prompt
    if reference_image:
        payload["reference_image"] = reference_image
    if generate_audio is not None:
        payload["generate_audio"] = generate_audio
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
