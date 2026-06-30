#!/usr/bin/env python3
"""Part 3+4: reconstruct per-call decision events from LINEDEDUP/GENTLE6K ledgers + C0 baseline.
Honestly classify counterfactual availability — observational runs are NOT randomized event-level."""
import json, os, glob, hashlib
BASE="/data/users/dengcchi/prune_ab"
G=set(json.load(open("/tmp/golden50.json")))

def ledger_events(method, ledger):
    """each call = a decision event with pre/post token state + activation."""
    evs=[]
    if not os.path.exists(ledger): return evs
    for l in open(ledger):
        try:
            d=json.loads(l); t=d.get("task_id")
            if not t or str(t).startswith(("UNKNOWN","NO_")): continue
            evs.append({
                "task_id":t,"repo":t.split("__")[0],"method":method,
                "call_index":d.get("call_index"),
                "action":"FIRED" if d.get("changed") else "NO_OP_ELIGIBLE",
                "action_fired":bool(d.get("changed")),
                "chars_removed":d.get("characters_removed",0),
                "tokens_removed_est":d.get("tokens_removed_estimate",0),
                "first_changed_msg_idx":d.get("first_changed_message_index"),
                "messages_before_tokens":d.get("messages_before_tokens"),
                # local outcome at this call:
                "cache_read":d.get("cache_read_tokens"),"cache_creation":d.get("cache_creation_tokens"),
                "output_tokens":d.get("output_tokens"),"latency":d.get("latency_seconds"),
                "timestamp":d.get("timestamp"),
            })
        except: pass
    return evs

events=[]
for m,led in [("LINEDEDUP_e4","logs/e4/ledger_LINEDEDUP_e4.jsonl"),
              ("GENTLE6K_stable","logs/stable/ledger_GENTLE6K_stable.jsonl"),
              ("RETRIEVREF_e4","logs/e4/ledger_RETRIEVREF_e4.jsonl")]:
    events += ledger_events(m, f"{BASE}/{led}")

# classify counterfactual availability
# C0 ran the SAME tasks but NOT the same trajectory (no per-call paired counterfactual)
for e in events:
    # Is there a matching C0 call at the same prefix? NO — once a method fires, the trajectory diverges.
    # Even call_index 0 is identical (no pruning yet), but later calls diverge.
    if e["call_index"]==0 or not e["action_fired"]:
        e["counterfactual"]="PAIRED_TASK_ONLY"  # task-level C0 exists, not event-level
    else:
        e["counterfactual"]="COUNTERFACTUAL_UNIDENTIFIED"  # post-divergence, no matched C0 state
    e["data_completeness"]="ledger_only"  # no segment content stored, no reread tracking

with open(f"{BASE}/results/pruning_ab/decision_event_manifest.jsonl","w") as fo:
    for e in events: fo.write(json.dumps(e)+"\n")

from collections import Counter
print(f"reconstructed {len(events)} decision events from observational runs")
print(f"by method: {dict(Counter(e['method'] for e in events))}")
print(f"action fired: {sum(e['action_fired'] for e in events)}/{len(events)}")
print(f"\ncounterfactual availability:")
for k,v in Counter(e['counterfactual'] for e in events).items(): print(f"  {k}: {v}")
print(f"\n=== HONEST FINDING ===")
print("Observational method runs provide NO randomized event-level counterfactuals.")
print("Once a method fires at call k, the trajectory DIVERGES from C0 -> no matched C0 state")
print("at call k+1. We have PAIRED_TASK_ONLY (task-level C0) and COUNTERFACTUAL_UNIDENTIFIED")
print("(post-divergence calls). Event-level CATE is NOT identifiable from current runs.")
print("=> A micro-randomized trial is REQUIRED for event-level causal effects (Part 6).")
