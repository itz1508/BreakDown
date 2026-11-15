"""OneShot agents package entrypoint: choose a role module to run."""

from __future__ import annotations

import sys

_USAGE = (
    "usage: python -m agents.<role> ... where <role> is one of: "
    "skills.researcher, skills.auditor, skills.planner, skills.builder, "
    "skills.coder, skills.spec_search. Each role reads one JSON request "
    "from stdin and writes one JSON response to stdout."
)


def main() -> int:
    print(_USAGE, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
