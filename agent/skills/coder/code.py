"""Standalone CodeDesign question CLI: python -m agent.skills.coder.

Read-only: generates evidence questions for an existing, validated CodeDesign
candidate. Does not dispatch a stage, choose a final design, or issue receipts.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agent.skills.coder.coding import review_questions


def main() -> int:
    parser = argparse.ArgumentParser(description="CodeDesign evidence questions (read-only guidance)")
    parser.add_argument("--design-file", type=Path, required=True, help="CodeDesign JSON file")
    args = parser.parse_args()

    from pydantic import TypeAdapter

    from agent.skills.auditor.contracts.code_design import CodeDesign

    try:
        design = TypeAdapter(CodeDesign).validate_json(args.design_file.read_bytes())
    except (OSError, ValueError) as exc:
        parser.error(f"invalid CodeDesign file: {type(exc).__name__}: {exc}")
    questions = review_questions(design)
    print(
        json.dumps(
            [q.__dict__ for q in questions],
            sort_keys=True,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
