#!/usr/bin/env python3
"""Cache-aware effective-cost analysis for the stable-pruning experiment.
EFFECTIVE COST = input*1.0 + cache_read*0.1 + cache_creation*1.25 + output*5.0  (Anthropic pricing units)
Paired per-task vs C0 baseline. The metric that decides if pruning achieves TRUE task-level saving."""
import json, glob, os, statistics as st, math
BASE="/data/users/dengcchi/prune_ab"

def eff_cost_per_task_from_ledger(ledger_path):
    """sum effective cost per task_id from a task-tagged ledger."""
    if not os.path.exists(ledger_path): return {}
    agg={}
    for l in open(ledger_path):
        try:
            d=json.loads(l); t=d.get("task_id")
            if not t or str(t).startswith("UNKNOWN") or str(t).startswith("NO_"): continue
            ec=(d.get("input_tokens") or 0)*1.0 + (d.get("cache_read_tokens") or 0)*0.1 \
               + (d.get("cache_creation_tokens") or 0)*1.25 + (d.get("output_tokens") or 0)*5.0
            a=agg.setdefault(t,{"eff":0,"cr":0,"cc":0,"out":0,"calls":0})
            a["eff"]+=ec; a["cr"]+=(d.get("cache_read_tokens") or 0); a["cc"]+=(d.get("cache_creation_tokens") or 0)
            a["out"]+=(d.get("output_tokens") or 0); a["calls"]+=1
        except: pass
    return agg

def resolved(grade_path):
    return set(json.load(open(grade_path)).get("resolved_ids",[])) if os.path.exists(grade_path) else None

def wilson_upper(k,n,z=1.645):
    if n==0: return 1.0
    p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d; m=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return min(1.0,c+m)

# C0 baseline: from the ORIGINAL full-50 ledger? It's contaminated. Better: we need a clean C0 task-tagged ledger.
# We have phase34 C0 (10 tasks) and the held-out. For golden-50 we DON'T have a clean tagged C0 ledger.
# SOLUTION: the stable runs' OWN cache behavior tells the story. But for paired cost we need C0 per-task.
# Use SWE-agent traj model_stats as the cross-check (tokens_sent + cost), AND the stable ledger cache ratio.

golden=set(json.load(open(f"{BASE}/heldout_tasks.json")[:0] or f"{BASE}/../prune_ab/dummy") ) if False else set(json.load(open("/tmp/golden50.json")))

# C0 cache profile from its clean phase34 ledgers (per-call cache ratio is method-intrinsic)
def method_cache_ratio_and_eff(method, ledger_glob):
    cr=cc=ec=ir=op=0
    for f in glob.glob(ledger_glob):
        for l in open(f):
            try:
                d=json.loads(l)
                cr+=(d.get("cache_read_tokens") or d.get("cache_read") or 0)
                cc+=(d.get("cache_creation_tokens") or d.get("cache_creation") or 0)
                ir+=(d.get("input_tokens") or d.get("input") or 0)
                op+=(d.get("output_tokens") or d.get("output") or 0)
            except: pass
    ec=ir*1.0+cr*0.1+cc*1.25+op*5.0
    return {"cache_read":cr,"cache_creation":cc,"ratio":round(cr/max(cc,1),2),"eff_cost":ec,"output":op}

print("=== CACHE-AWARE EFFECTIVE COST: stable methods vs C0 ===\n")
print(f"{'method':18s}{'cr:cc ratio':>12s}{'eff_cost':>14s}{'vs C0 eff':>12s}")
c0=method_cache_ratio_and_eff("C0", f"{BASE}/logs/phase34/ledger_C0_identity_rep*.jsonl")
print(f"{'C0_identity':18s}{c0['ratio']:>12.2f}{c0['eff_cost']:>14,.0f}{'(baseline)':>12s}")
for m in ["CAP1K_stable","CAP800_stable","CAP500_stable","SMART_stable","COMBOSC_stable"]:
    p=method_cache_ratio_and_eff(m, f"{BASE}/logs/stable/ledger_{m}.jsonl")
    if p["eff_cost"]>0:
        # note: not yet per-task-normalized; this is aggregate over whatever ran
        print(f"{m:18s}{p['ratio']:>12.2f}{p['eff_cost']:>14,.0f}")
print("\n(ratio >> 1 = cache preserved = GOOD. The stable methods should stay HIGH like C0's, not crash to 0.37 like HYBRID1.)")
print("NOTE: per-task paired cost computed separately once grades land; this is the cache-health check.")
