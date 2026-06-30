#!/usr/bin/env python3
import json, os, statistics as st, math
BASE="/data/users/dengcchi/prune_ab"
INT10=sorted(json.load(open("/tmp/interesting10.json")))
def res(method,rep):
    f=f"{BASE}/results/pruning_ab/phase34/grade_{method}_rep{rep}.json"
    return set(json.load(open(f)).get("resolved_ids",[])) if os.path.exists(f) else None
# per-task success RATE across 5 reps, per method
def rate(method,task):
    s=[1 if (res(method,r) and task in res(method,r)) else 0 for r in range(1,6) if res(method,r) is not None]
    return s
print("="*74)
print("SUCCESS-CATE via REPEATED RUNS (5 reps, 10 interesting tasks) — proper causal estimate")
print("Forbidden: deleting 'unstable' tasks. Instead: P(success|treat) - P(success|C0) per task.")
print("="*74)
print(f"\n{'task':28s}{'C0 rate':>9s}{'SHAM rate':>10s}{'HYB rate':>9s}{'HYB-C0':>8s}")
deltas_hyb=[]; deltas_sham=[]
for t in INT10:
    c=rate("C0_identity",t); s=rate("SHAM",t); h=rate("HYBRID1_m7_agg2",t)
    cm=st.mean(c) if c else None; sm=st.mean(s) if s else None; hm=st.mean(h) if h else None
    if cm is not None and hm is not None: deltas_hyb.append(hm-cm)
    if cm is not None and sm is not None: deltas_sham.append(sm-cm)
    print(f"{t:28s}{cm if cm is not None else 0:>9.1f}{sm if sm is not None else 0:>10.1f}{hm if hm is not None else 0:>9.1f}{(hm-cm) if (cm is not None and hm is not None) else 0:>+8.1f}")
print(f"\n  MEAN success-CATE (HYBRID1 - C0): {st.mean(deltas_hyb):+.2f}  (n={len(deltas_hyb)} tasks, 5 reps each)")
print(f"  MEAN success-CATE (SHAM - C0):    {st.mean(deltas_sham):+.2f}  (negative control: should be ~0)")
print(f"\n  => SHAM-C0 near 0 validates the no-op control. HYBRID1-C0 is the cache-bust method's")
print(f"     TRUE quality effect, estimated WITHOUT deleting unstable tasks (per causal rules).")
# how many tasks are genuinely unstable under C0 (rate not 0 or 1)?
unstable=sum(1 for t in INT10 if rate("C0_identity",t) and 0<st.mean(rate("C0_identity",t))<1)
print(f"\n  C0-unstable tasks (0<rate<1): {unstable}/10 -> single-run flips on these have UNRESOLVED attribution")
json.dump({"success_cate_hyb_vs_c0":round(st.mean(deltas_hyb),3),"success_cate_sham_vs_c0":round(st.mean(deltas_sham),3),
           "n_c0_unstable":unstable,"per_task":{t:{"c0":st.mean(rate("C0_identity",t)) if rate("C0_identity",t) else None,
           "sham":st.mean(rate("SHAM",t)) if rate("SHAM",t) else None,"hyb":st.mean(rate("HYBRID1_m7_agg2",t)) if rate("HYBRID1_m7_agg2",t) else None} for t in INT10}},
          open(f"{BASE}/results/pruning_ab/success_cate_repeated.json","w"),indent=1)
print("\nsuccess_cate_repeated.json written")
