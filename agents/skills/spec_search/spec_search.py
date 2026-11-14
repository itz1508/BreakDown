"""CLI: python -m agents.skills.spec_search --root . --term TokenBucket"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from agents.skills.spec_search.spec_searching import (
    DEFAULT_SUFFIXES,
    SpecQuery,
    SpecSearchError,
    search,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m agents.skills.spec_search",
        description="Read-only specification evidence search (no model, no writes)",
    )
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Authorized repository root")
    parser.add_argument("--scope", default=".", help="Relative in-repository directory")
    parser.add_argument("--term", action="append", required=True, help="Search term; repeatable")
    parser.add_argument("--suffix", action="append", default=None, help="File suffix; repeatable")
    parser.add_argument("--max-results", type=int, default=20)
    parser.add_argument("--max-files", type=int, default=500)
    parser.add_argument("--max-file-bytes", type=int, default=1_000_000)
    parser.add_argument("--context-lines", type=int, default=2)
    args = parser.parse_args(argv)

    try:
        query = SpecQuery(
            terms=tuple(args.term),
            scope=args.scope,
            suffixes=tuple(args.suffix) if args.suffix else DEFAULT_SUFFIXES,
            max_results=args.max_results,
            max_files=args.max_files,
            max_file_bytes=args.max_file_bytes,
            context_lines=args.context_lines,
        )
        result = search(args.root, query)
    except (OSError, SpecSearchError) as exc:
        print(f"spec search refused: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
