#!/usr/bin/env python3
import json, os, statistics as st
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
c0=eff(f"{BASE}/logs/stable/ledger_C0_identity.jsonl")
ld=eff(f"{BASE}/logs/e4/ledger_LINEDEDUP_e4.jsonl")
g6=eff(f"{BASE}/logs/stable/ledger_GENTLE6K_stable.jsonl")
common=sorted(set(c0)&set(ld)&set(g6)&set(feats))
print(f"tasks with all 3 methods + features: {len(common)}")
def total(d,ts): return sum(d[t] for t in ts)
c0t=total(c0,common)
print(f"\n=== ORACLE GAP (total effective cost over {len(common)} tasks, lower=better) ===")
pol={}
pol["always_C0"]=c0t
pol["always_LINEDEDUP"]=total(ld,common)
pol["always_GENTLE6K"]=total(g6,common)
# oracle: per task, pick min(C0,LD,G6) using POST-HOC outcome (upper bound, not deployable)
pol["oracle_posthoc"]=sum(min(c0[t],ld[t],g6[t]) for t in common)
# deployable dup-threshold policy (Tier-1 feature): if dup_ratio>thr use LINEDEDUP else C0
for thr in [0.20,0.25,0.30]:
    pol[f"dup>{thr}->LD"]=sum(ld[t] if feats[t]["dup_line_ratio"]>thr else c0[t] for t in common)
for name,v in pol.items():
    print(f"  {name:22s} total={v:>14,.0f}  saving_vs_C0={100*(c0t-v)/c0t:+6.1f}%")
print(f"\n  ORACLE saving = {100*(c0t-pol['oracle_posthoc'])/c0t:+.1f}% (post-hoc upper bound, NOT deployable)")
print(f"  Best STATIC = {max(100*(c0t-pol['always_LINEDEDUP'])/c0t, 100*(c0t-pol['always_GENTLE6K'])/c0t):+.1f}%")
print(f"  Best deployable dup-threshold = {max(100*(c0t-pol[f'dup>{t}->LD'])/c0t for t in [0.2,0.25,0.3]):+.1f}%")
print(f"\n  DECISION: if oracle barely beats best-static, OR threshold can't beat best-static -> controller NOT justified")
json.dump({k:round(v,0) for k,v in pol.items()} | {"c0_total":round(c0t,0),"n":len(common)},
          open(f"{BASE}/results/pruning_ab/controller_policies.json","w"),indent=1)
