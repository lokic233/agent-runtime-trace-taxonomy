#!/usr/bin/env python3
"""Shared ledger loader with resume-dedup.

Cells resume-in-place across intermittent SIGKILLs: sweagent skips already-complete tasks (no new rows),
but a task killed mid-run re-runs and appends fresh rows on resume. Since call_index is per-task and resets
to 0 each shim-process, we dedup by (task_id, call_index) keeping the LAST occurrence — the final complete
run's rows overwrite any earlier partial rows for the same task. Tasks that never re-ran keep their rows.
"""
import json

def load_ledger_dedup(path):
    """Return the deduped list of call records for a cell ledger (last-write-wins per task_id+call_index)."""
    last = {}
    order = []
    for line in open(path):
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        key = (r.get("task_id"), r.get("call_index"))
        if key not in last:
            order.append(key)
        last[key] = r
    return [last[k] for k in order]
