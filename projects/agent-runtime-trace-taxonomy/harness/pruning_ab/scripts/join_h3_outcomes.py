#!/usr/bin/env python3
"""Join H=3 cumulative outcomes offline from an immutable events.jsonl.
For each experimental event (the intervention), sum effective_cost_h1 over the intervention
response and the next up-to-2 main-agent responses of the SAME task (by call_index order).
Records terminal state + observed horizon when a task terminates before H=3.
Never mutates the raw events log."""
import json, sys, collections, os

def load_events(path):
    return [json.loads(l) for l in open(path) if l.strip()]

def join_h3(events):
    # group logged (non-None rec) events by task, ordered by call_index
    by_task = collections.defaultdict(list)
    for e in events:
        if e.get("task_id"):
            by_task[e["task_id"]].append(e)
    out = []
    for tid, evs in by_task.items():
        evs.sort(key=lambda e: e.get("call_index", 0))
        # find the experimental event
        exp = [e for e in evs if e.get("experimental_event")]
        if not exp:
            continue
        iv = exp[0]
        # all events at or after the intervention call_index for this task
        after = [e for e in evs if e.get("call_index", 0) >= iv.get("call_index", 0)]
        horizon = after[:3]
        costs = [e.get("effective_cost_h1") for e in horizon if e.get("effective_cost_h1") is not None]
        infra_fail = any(e.get("infrastructure_failure") for e in horizon)
        rec = {
            "task_id": tid,
            "event_id": iv.get("event_id"),
            "assignment": iv.get("assignment"),
            "moderator_stratum": iv.get("moderator_stratum"),
            "duplicate_line_fraction": iv.get("duplicate_line_fraction"),
            "block_id": iv.get("block_id"),
            "propensity": iv.get("propensity"),
            "effective_cost_h1": iv.get("effective_cost_h1"),
            "effective_cost_h3": sum(costs) if costs else None,
            "observed_horizon": len(horizon),
            "terminated_before_h3": len(horizon) < 3,
            "h3_infrastructure_failure": infra_fail,
            # rework proxies over the horizon
            "h3_calls": len(horizon),
            "h3_output_tokens": sum((e.get("output_tokens") or 0) for e in horizon),
            "h3_cache_read_tokens": sum((e.get("cache_read_tokens") or 0) for e in horizon),
            "h3_cache_creation_tokens": sum((e.get("cache_creation_tokens") or 0) for e in horizon),
            "h3_latency_seconds": sum((e.get("latency_seconds") or 0) for e in horizon),
        }
        out.append(rec)
    return out

if __name__ == "__main__":
    ev_path = sys.argv[1] if len(sys.argv) > 1 else "results/pruning_ab/mrt_formal/events.jsonl"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "results/pruning_ab/mrt_formal/h3_outcomes.jsonl"
    events = load_events(ev_path)
    joined = join_h3(events)
    with open(out_path, "w") as f:
        for r in joined:
            f.write(json.dumps(r) + "\n")
    print(f"joined {len(joined)} intervention H=3 records -> {out_path}")
    for r in joined:
        print(f"  {r['task_id'][:24]} {r['assignment']:9s} stratum={r['moderator_stratum']:16s} "
              f"h1={r['effective_cost_h1']} h3={r['effective_cost_h3']} horizon={r['observed_horizon']}")
