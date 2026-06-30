#!/usr/bin/env python3
import json, os
BASE="/data/users/dengcchi/prune_ab"
G=set(json.load(open("/tmp/golden50.json")))
def ledger_by_task(led):
    d={}
    for l in open(f"{BASE}/{led}"):
        try:
            x=json.loads(l);t=x.get("task_id")
            if not t or str(t).startswith(("UNKNOWN","NO_")):continue
            d.setdefault(t,[]).append(x)
        except:pass
    for t in d: d[t].sort(key=lambda r:r.get("call_index",0))
    return d
c0=ledger_by_task("logs/stable/ledger_C0_identity.jsonl")
ld=ledger_by_task("logs/e4/ledger_LINEDEDUP_e4.jsonl")
# For each task, find first call where LINEDEDUP fired (first divergence)
print("=== identical-prefix window (pre-first-fire = matched to C0) ===")
matched_calls=0; tasks_with_window=0
for t in set(c0)&set(ld):
    first_fire=next((r["call_index"] for r in ld[t] if r.get("changed")), None)
    if first_fire is None: 
        # never fired -> entire run is ~identical to C0 (modulo nondeterminism)
        continue
    if first_fire>0:
        tasks_with_window+=1; matched_calls+=first_fire
print(f"tasks where LINEDEDUP fired at call>0 (have a pre-fire matched window): {tasks_with_window}")
print(f"total matched pre-fire calls (identical prefix to C0): {matched_calls}")
print(f"\n  => even these aren't a clean EVENT-level counterfactual: the FIRE itself is the treatment,")
print(f"     and there's no C0 run that experienced the identical prefix THEN got pruned vs not.")
print(f"     Agent nondeterminism (temp can vary) also means 'identical prefix' isn't guaranteed.")
print(f"\n=== CONCLUSION: event-level CATE = COUNTERFACTUAL_UNIDENTIFIED from observational data ===")
print(f"  The honest path is a micro-randomized trial (Part 6) where the SAME prefix is")
print(f"  randomly assigned FIRE vs NO_OP, creating matched event-level counterfactuals.")
