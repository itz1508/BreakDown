"""Coder CLI: print evidence questions for a CodeDesign intent origin."""

from __future__ import annotations

import argparse
import json
import sys

from agent.skills.coder.coding import DesignQuestion, _BASE_QUESTIONS, _ORIGIN_QUESTIONS


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Print CodeDesign evidence questions for a given intent origin."
    )
    parser.add_argument(
        "--origin",
        default="existing_implementation_gap",
        choices=tuple(_ORIGIN_QUESTIONS),
        help="Intent origin for the CodeDesign candidate",
    )
    args = parser.parse_args()
    questions = _BASE_QUESTIONS + _ORIGIN_QUESTIONS[args.origin]
    rows = [
        {"key": q.key, "question": q.question, "evidence_needed": q.evidence_needed, "concern": q.concern_if_unresolved}
        for q in questions
    ]
    print(json.dumps(rows, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
