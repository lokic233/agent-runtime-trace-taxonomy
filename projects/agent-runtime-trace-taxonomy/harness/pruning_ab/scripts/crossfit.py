#!/usr/bin/env python3
import json, os, statistics as st
from collections import defaultdict
BASE="/data/users/dengcchi/prune_ab"
G=set(json.load(open("/tmp/golden50.json")))
feats={r["task_id"]:r for r in (json.loads(l) for l in open(f"{BASE}/results/pruning_ab/pre_treatment_features.jsonl"))}
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
c0=eff("logs/stable/ledger_C0_identity.jsonl");ld=eff("logs/e4/ledger_LINEDEDUP_e4.jsonl");g6=eff("logs/stable/ledger_GENTLE6K_stable.jsonl")
common=sorted(set(c0)&set(ld)&set(g6)&set(feats))
byrepo=defaultdict(list)
for t in common: byrepo[feats[t]["repo"]].append(t)
repos=sorted(byrepo)

print("="*72)
print("PHASE 4C: LEAVE-ONE-REPOSITORY-OUT controller cross-fitting (no in-sample leakage)")
print("="*72)
# For each held-out repo: learn best dup-threshold on the OTHER repos, apply to held-out, measure saving
def policy_cost(tasks, thr):
    return sum(ld[t] if feats[t]["dup_line_ratio"]>thr else c0[t] for t in tasks)
def static_best_cost(tasks):
    # best static among C0/LD/G6 learned on training, applied to held-out
    return None
thresholds=[0.15,0.18,0.20,0.22,0.25,0.30,0.35]
loro_policy=0; loro_c0=0; loro_g6=0; loro_ld=0; total_c0=0
for held in repos:
    train=[t for r in repos if r!=held for t in byrepo[r]]
    test=byrepo[held]
    # learn best threshold on train
    best_thr=min(thresholds, key=lambda th: policy_cost(train,th))
    # also learn best static on train (which constant method is cheapest on train)
    statics={"C0":sum(c0[t] for t in train),"LD":sum(ld[t] for t in train),"G6":sum(g6[t] for t in train)}
    best_static=min(statics,key=statics.get)
    # apply to TEST (held-out repo)
    loro_policy+=policy_cost(test,best_thr)
    loro_c0+=sum(c0[t] for t in test)
    sb={"C0":c0,"LD":ld,"G6":g6}[best_static]
    loro_g6+=sum(sb[t] for t in test)  # best-static-from-train applied to test
    total_c0+=sum(c0[t] for t in test)
print(f"\nLeave-one-repo-out aggregate (policy learned on train repos, applied to held-out repo):")
print(f"  always_C0:                {total_c0:>12,.0f}  (+0.0%)")
print(f"  trace policy (LORO):      {loro_policy:>12,.0f}  ({100*(total_c0-loro_policy)/total_c0:+.1f}%)")
print(f"  best-static-from-train:   {loro_g6:>12,.0f}  ({100*(total_c0-loro_g6)/total_c0:+.1f}%)")
print(f"\n  => out-of-sample (LORO), does trace policy beat best-static-from-train?")
verdict = "YES (controller has value)" if loro_policy<loro_g6 else "NO (controller does NOT beat best-static out-of-sample)"
print(f"  VERDICT: {verdict}")
json.dump({"loro_c0":round(total_c0),"loro_trace_policy":round(loro_policy),"loro_best_static":round(loro_g6),
           "trace_saving_pct":round(100*(total_c0-loro_policy)/total_c0,1),"static_saving_pct":round(100*(total_c0-loro_g6)/total_c0,1),
           "controller_beats_static_OOS": loro_policy<loro_g6},
          open(f"{BASE}/results/pruning_ab/controller_crossfit.json","w"),indent=1)
print("\ncontroller_crossfit.json written")
