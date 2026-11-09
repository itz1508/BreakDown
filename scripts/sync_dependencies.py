import shutil
import subprocess
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    uv = shutil.which("uv")

    if uv is None:
        raise RuntimeError("uv is not installed. Install uv first.")

    for name in ("pyproject.toml", "uv.lock"):
        if not (root / name).is_file():
            raise RuntimeError(f"Missing {name}")

    # Use existing project declarations and default dependency groups.
    command = [uv, "sync", "--locked"]

    subprocess.run([*command, "--dry-run"], cwd=root, check=True)
    subprocess.run(command, cwd=root, check=True)
    subprocess.run([*command, "--check"], cwd=root, check=True)


if __name__ == "__main__":
    main()
