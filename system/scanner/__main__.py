"""CLI: python -m system.scanner <target> [--mode debug|preflight|predict]

Writes exactly one JSON report document to stdout. Diagnostics go to stderr.
Read-only: the scan never writes to the target or anywhere else.
"""

from __future__ import annotations

import argparse
import json
import sys

from system.scanner._debug import scan_debug
from system.scanner._predict import scan_predict
from system.scanner._preflight import scan_preflight


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="system.scanner", description="Read-only static scanner")
    parser.add_argument("target", help="Directory to scan")
    parser.add_argument("--mode", choices=["debug", "preflight", "predict"], default="debug")
    parser.add_argument("--ledger", default="", help="Path to a JSON file containing retired-path prefixes")
    parser.add_argument("--baseline", default="", help="Path to a JSON file containing baseline entries")
    parser.add_argument("--max-file-bytes", type=int, default=None)
    options = parser.parse_args(argv)

    if options.mode == "preflight":
        retired: tuple[str, ...] = ()
        if options.ledger:
            with open(options.ledger, encoding="utf-8") as handle:
                retired = tuple(json.load(handle))
        report = scan_preflight(options.target, retired_prefixes=retired)
    elif options.mode == "predict":
        if not options.baseline:
            print("--baseline is required for predict mode", file=sys.stderr)
            return 2
        with open(options.baseline, encoding="utf-8") as handle:
            baseline = tuple(
                (entry["relative_path"], entry["sha256"], entry["size_bytes"]) for entry in json.load(handle)
            )
            from system.scanner._types import FileEntry

            baseline_entries = tuple(FileEntry(*entry) for entry in baseline)
        if options.max_file_bytes is None:
            report = scan_predict(baseline_entries, options.target)
        else:
            report = scan_predict(baseline_entries, options.target, max_file_bytes=options.max_file_bytes)
    else:
        if options.max_file_bytes is None:
            report = scan_debug(options.target)
        else:
            report = scan_debug(options.target, max_file_bytes=options.max_file_bytes)

    json.dump(report.to_dict(), sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
