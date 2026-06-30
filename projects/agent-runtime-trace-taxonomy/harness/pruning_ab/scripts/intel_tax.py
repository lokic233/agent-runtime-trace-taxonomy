#!/usr/bin/env python3
"""Mechanism B: intelligence tax. Drift (extra calls/output) as fn of WHAT is removed, not how much."""
import json, os, glob, statistics as st
BASE="/data/users/dengcchi/prune_ab"
G=set(json.load(open("/tmp/golden50.json")))

def task_stats(arm):
    """per-task api_calls + output tokens from trajs."""
    d={}
    for f in glob.glob(f"{BASE}/arms/{arm}/*/*.traj"):
        tid=os.path.basename(f).replace(".traj","")
        if tid not in G: continue
        try:
            ms=json.load(open(f))["info"]["model_stats"]
            d[tid]={"calls":ms.get("api_calls",0),"out":ms.get("tokens_received",0),"sent":ms.get("tokens_sent",0)}
        except: pass
    return d

def chars_removed(ledger):
    """median per-call chars removed (the 'dose') from task-tagged ledger."""
    if not os.path.exists(ledger): return None
    cr=[]
    for l in open(ledger):
        try:
            d=json.loads(l)
            if d.get("changed"): cr.append(d.get("characters_removed",0))
        except: pass
    return st.median(cr) if cr else 0

c0=task_stats("stable_C0_identity")
print("="*72)
print("MECHANISM B: INTELLIGENCE TAX — drift (extra calls) vs WHAT is removed")
print("="*72)
print(f"\n{'method':16s}{'removal_type':16s}{'med_dose(chars)':>16s}{'call_ratio':>11s}{'out_ratio':>10s}")
# methods grouped by removal TYPE
methods=[
 ("LINEDEDUP_e4","exact-duplicate","logs/e4/ledger_LINEDEDUP_e4.jsonl","e4_LINEDEDUP_e4"),
 ("RETRIEVREF_e4","retrievable-ref","logs/e4/ledger_RETRIEVREF_e4.jsonl","e4_RETRIEVREF_e4"),
 ("GENTLE6K_stable","outlier-truncate","logs/stable/ledger_GENTLE6K_stable.jsonl","stable_GENTLE6K_stable"),
 ("CAP1K_stable","uniform-truncate","logs/stable/ledger_CAP1K_stable.jsonl","stable_CAP1K_stable"),
 ("CAP500_stable","uniform-truncate","logs/stable/ledger_CAP500_stable.jsonl","stable_CAP500_stable"),
 ("SIGNAL_e4","signal-line-skim","logs/e4/ledger_SIGNAL_e4.jsonl","e4_SIGNAL_e4"),
]
rows=[]
for name,rtype,led,arm in methods:
    ts=task_stats(arm); common=sorted(set(c0)&set(ts))
    if len(common)<10: continue
    callr=st.median([ts[t]["calls"]/max(c0[t]["calls"],1) for t in common])
    outr=st.median([ts[t]["out"]/max(c0[t]["out"],1) for t in common])
    dose=chars_removed(f"{BASE}/{led}")
    rows.append({"method":name,"type":rtype,"dose":dose,"call_ratio":round(callr,2),"out_ratio":round(outr,2),"n":len(common)})
    print(f"{name:16s}{rtype:16s}{(dose or 0):>16.0f}{callr:>11.2f}{outr:>10.2f}")
print("\n  KEY TEST: at SIMILAR dose, does removal TYPE change drift (call_ratio)?")
print("  - exact-duplicate removal (LINEDEDUP): should be ~1.0 (no new info lost)")
print("  - uniform/signal truncation (CAP/SIGNAL): should be >1.0 (drops unique content -> re-fetch)")
print("  This separates the INTELLIGENCE TAX (what) from the DOSE (how much).")
import json as J
m=J.load(open(f"{BASE}/results/pruning_ab/mechanism_effects.json"))
m["intelligence_tax"]=rows
J.dump(m, open(f"{BASE}/results/pruning_ab/mechanism_effects.json","w"), indent=1, default=str)
print("\nmechanism_effects.json (intelligence tax) updated")
