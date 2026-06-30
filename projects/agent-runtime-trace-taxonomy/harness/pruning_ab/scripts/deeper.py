#!/usr/bin/env python3
import json, os, statistics as st, random
BASE="/data/users/dengcchi/prune_ab"
G=set(json.load(open("/tmp/golden50.json")))
feats={r["task_id"]:r for r in (json.loads(l) for l in open(f"{BASE}/results/pruning_ab/pre_treatment_features.jsonl"))}
def eff(led):
    a={}
    for l in open(led):
        try:
            d=json.loads(l);t=d.get("task_id")
            if not t or str(t).startswith(("UNKNOWN","NO_")):continue
            ir=(d.get("input_tokens")or 0);cr=(d.get("cache_read_tokens")or 0);cc=(d.get("cache_creation_tokens")or 0);op=(d.get("output_tokens")or 0)
            a[t]=a.get(t,0)+ir+cr*.1+cc*1.25+op*5
        except:pass
    return a
c0=eff(f"{BASE}/logs/stable/ledger_C0_identity.jsonl"); ld=eff(f"{BASE}/logs/e4/ledger_LINEDEDUP_e4.jsonl")
common=sorted(set(c0)&set(ld)&set(feats))
print(f"LINEDEDUP paired tasks: {len(common)}")
# task-weighted vs bill-weighted
ds=[100*(c0[t]-ld[t])/c0[t] for t in common if c0[t]>0]
ct=sum(c0[t] for t in common); lt=sum(ld[t] for t in common)
print(f"  task-weighted MEAN saving: {st.mean(ds):+.1f}% | MEDIAN: {st.median(ds):+.1f}%")
print(f"  bill-weighted (overall) saving: {100*(ct-lt)/ct:+.1f}%")
print(f"  => the +6.3% headline is BILL-weighted; per-task it's {st.median(ds):+.1f}% median (near 0)")
print(f"  => the aggregate win comes from a FEW big tasks, not a typical task. Hostile review notes this.")

print("\n=== LEAVE-ONE-REPO-OUT: does dup_ratio predict LINEDEDUP saving WITHIN repos? ===")
from collections import defaultdict
byrepo=defaultdict(list)
for t in common: byrepo[feats[t]["repo"]].append(t)
# within-repo spearman (controls the repo confound)
def _rank(v):
    idx=sorted(range(len(v)),key=lambda i:v[i]); r=[0]*len(v)
    for rk,i in enumerate(idx): r[i]=rk
    return r
def sp(ts):
    if len(ts)<4: return None
    xs=[feats[t]["dup_line_ratio"] for t in ts]; ys=[100*(c0[t]-ld[t])/c0[t] for t in ts]
    rx=_rank(xs);ry=_rank(ys);n=len(xs);d2=sum((rx[i]-ry[i])**2 for i in range(n))
    return 1-6*d2/(n*(n*n-1))
within=[]
for repo,ts in sorted(byrepo.items()):
    s=sp(ts)
    if s is not None: within.append(s); print(f"  {repo:16s} n={len(ts)} within-repo spearman(dup,saving)={s:+.2f}")
if within: print(f"  MEAN within-repo spearman = {st.mean(within):+.2f}  (vs cross-repo +0.19)")
print("  => if within-repo correlation ~0, dup_ratio's signal was a REPO confound, not causal.")
