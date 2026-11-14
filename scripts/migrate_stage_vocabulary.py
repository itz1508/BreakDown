"""Versioned stage-vocabulary migration for persisted workflow state.

Migrates persisted stage identifiers from the retired six-stage vocabulary to
the v3 breakdown workflow (agent/breakdown.yaml, definition_version: 3).
Idempotent: records a migration marker and refuses to run twice for the same
target version.

Receipt subjects are stored only as digests, so a non-empty receipts database
cannot be textually migrated; the script fails closed and requires re-issuing
receipts instead of guessing.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

TARGET_VERSION = 3

# Retired six-stage vocabulary -> v3 stage ids.
STAGE_MAP = {
    "research": "research",
    "audit_discovery": "discovery",
    "planning": "planning",
    "fixture_validation": "preflight",
    "build": "sandbox_execution",
    # The retired final verification stage has no successor stage: validation
    # is out-of-band, so completed verification state maps to completion.
    "build_validation": "completion_and_retention",
}

_MARKER = "stage_vocabulary_migration_v3"


def _map_stage(value: str) -> str:
    return STAGE_MAP.get(value, value)


def _migrate_checkpoints(db: Path) -> int:
    con = sqlite3.connect(db)
    migrated = 0
    for task_id, revision, state_json in con.execute(
        "select task_id, revision, state_json from checkpoints"
    ).fetchall():
        state = json.loads(state_json)
        changed = False
        if state.get("current_stage") in STAGE_MAP:
            state["current_stage"] = _map_stage(state["current_stage"])
            changed = True
        stages = state.get("completed_stages")
        if isinstance(stages, list) and any(s in STAGE_MAP and STAGE_MAP[s] != s for s in stages):
            stages = [_map_stage(s) for s in stages]
            changed = True
        if changed:
            state["completed_stages"] = stages
            con.execute(
                "update checkpoints set state_json = ? where task_id = ? and revision = ?",
                (json.dumps(state), task_id, revision),
            )
            migrated += 1
    con.commit()
    con.close()
    return migrated


def _migrate_events(db: Path) -> int:
    con = sqlite3.connect(db)
    migrated = 0
    for seq, event_data in con.execute("select seq, event_data from events").fetchall():
        updated = event_data
        for old, new in STAGE_MAP.items():
            if old != new:
                updated = updated.replace(f":{old}:", f":{new}:").replace(f":{old}\n", f":{new}\n")
        if updated != event_data:
            con.execute("update events set event_data = ? where seq = ?", (updated, seq))
            migrated += 1
    con.commit()
    con.close()
    return migrated


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("state_root", help="State root containing the workflow databases")
    args = parser.parse_args()

    root = Path(args.state_root)
    marker = root / ".migrations"
    marker.mkdir(parents=True, exist_ok=True)
    done = marker / _MARKER
    if done.exists():
        print(f"migration {_MARKER} already applied to {root}")
        return 0

    receipts = root / "receipts.db"
    if receipts.exists():
        con = sqlite3.connect(receipts)
        count = con.execute("select count(*) from receipts").fetchone()[0]
        con.close()
        if count:
            print(
                f"refusing to migrate {root}: {count} receipt rows exist; receipt subjects are "
                "digest-only and must be re-issued against the v3 vocabulary"
            )
            return 1

    migrated = 0
    checkpoints = root / "checkpoints.db"
    if checkpoints.exists():
        migrated += _migrate_checkpoints(checkpoints)
    events = root / "events.db"
    if events.exists():
        migrated += _migrate_events(events)

    done.write_text(f"target_version={TARGET_VERSION}\nrows_updated={migrated}\n", encoding="utf-8")
    print(f"migration {_MARKER} applied: {migrated} rows updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
