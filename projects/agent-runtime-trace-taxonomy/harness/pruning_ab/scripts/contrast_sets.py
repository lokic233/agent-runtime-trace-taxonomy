#!/usr/bin/env python3
"""Phase 2: build contrast sets. Unit = task x call x segment. Group by outcome class.
Outcomes stored in a SEPARATE sealed file; the blind-annotation view exposes ONLY prefix info."""
import json, os, glob, hashlib
BASE="/data/users/dengcchi/prune_ab"
G=set(json.load(open("/tmp/golden50.json")))

def eff(led):
    a={}
    for l in open(f"{BASE}/{led}"):
        try:
            d=json.loads(l);t=d.get("task_id")
            if not t or str(t).startswith(("UNKNOWN","NO_")):continue
            ir=(d.get("input_tokens")or 0);cr=(d.get("cache_read_tokens")or 0);cc=(d.get("cache_creation_tokens")or 0);op=(d.get("output_tokens")or 0)
            a[t]=a.get(t,0)+ir+cr*.1+cc*1.25+op*5
        except:pass
    return a
def resolved(p): return set(json.load(open(f"{BASE}/{p}")).get("resolved_ids",[]))&G if os.path.exists(f"{BASE}/{p}") else set()

c0=eff("logs/stable/ledger_C0_identity.jsonl")
ld=eff("logs/e4/ledger_LINEDEDUP_e4.jsonl")
g6=eff("logs/stable/ledger_GENTLE6K_stable.jsonl")
c0r=resolved("results/pruning_ab/stable/grade_C0_identity.json")
ldr=resolved("results/pruning_ab/e4/grade_LINEDEDUP_e4.json")
g6r=resolved("results/pruning_ab/stable/grade_GENTLE6K_stable.json")

# classify each task into contrast classes (task-level; the discovery UNIT is the task's trajectory)
def cls(t):
    tags=[]
    if t in c0 and t in ld:
        d=100*(c0[t]-ld[t])/c0[t]
        tags.append("LINEDEDUP_helped" if d>5 else ("LINEDEDUP_hurt" if d<-5 else "LINEDEDUP_neutral"))
    if t in c0 and t in g6:
        d=100*(c0[t]-g6[t])/c0[t]
        tags.append("GENTLE6K_helped" if d>5 else ("GENTLE6K_hurt" if d<-5 else "GENTLE6K_neutral"))
    # regression/improvement flips vs C0
    if t in c0r and t not in ldr: tags.append("LINEDEDUP_regressed")
    if t not in c0r and t in ldr: tags.append("LINEDEDUP_improved")
    # cost magnitude
    if t in c0: tags.append("high_cost" if c0[t]>200000 else "ordinary_cost")
    return tags

# build contrast set rows (task-level, with the C0 traj span refs)
sets=[]; sealed_outcomes={}
for t in sorted(G):
    if t not in c0: continue
    traj=glob.glob(f"{BASE}/arms/stable_C0_identity/{t}/*.traj")
    sets.append({
        "event_id": f"{t}#task",
        "task_id": t, "repo": t.split("__")[0],
        "unit": "task_trajectory",
        "c0_traj_path": f"arms/stable_C0_identity/{t}/{t}.traj",
        "ld_traj_path": f"arms/e4_LINEDEDUP_e4/{t}/{t}.traj",
        "g6_traj_path": f"arms/stable_GENTLE6K_stable/{t}/{t}.traj",
        "has_repeated_runs": t in set(json.load(open("/tmp/interesting10.json"))),
        # NO OUTCOME exposed here
    })
    sealed_outcomes[f"{t}#task"]={
        "contrast_classes": cls(t),
        "c0_eff": round(c0.get(t,0)), "ld_eff": round(ld.get(t,0)), "g6_eff": round(g6.get(t,0)),
        "ld_saving_pct": round(100*(c0[t]-ld[t])/c0[t],1) if t in ld and c0[t]>0 else None,
        "g6_saving_pct": round(100*(c0[t]-g6[t])/c0[t],1) if t in g6 and c0[t]>0 else None,
        "c0_resolved": t in c0r, "ld_resolved": t in ldr, "g6_resolved": t in g6r,
    }
with open(f"{BASE}/results/pruning_ab/signal_discovery_contrast_sets.jsonl","w") as fo:
    for s in sets: fo.write(json.dumps(s)+"\n")
with open(f"{BASE}/results/pruning_ab/sealed_outcomes.json","w") as fo:
    json.dump(sealed_outcomes, fo, indent=1)
print(f"contrast sets: {len(sets)} task-units (outcomes sealed separately)")
from collections import Counter
allcls=Counter(c for v in sealed_outcomes.values() for c in v["contrast_classes"])
print("contrast class coverage:")
for c,n in allcls.most_common(): print(f"  {c}: {n}")
