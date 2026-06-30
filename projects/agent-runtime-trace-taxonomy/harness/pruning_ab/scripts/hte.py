#!/usr/bin/env python3
"""Phase 4: heterogeneous treatment effects. CATE(cost) by pre-treatment feature, with falsification."""
import json, os, glob, statistics as st, random
BASE="/data/users/dengcchi/prune_ab"
G=set(json.load(open("/tmp/golden50.json")))
feats={r["task_id"]:r for r in (json.loads(l) for l in open(f"{BASE}/results/pruning_ab/pre_treatment_features.jsonl"))}

def per_task_eff(ledger):
    agg={}
    if not os.path.exists(ledger): return agg
    for l in open(ledger):
        try:
            d=json.loads(l);t=d.get("task_id")
            if not t or str(t).startswith(("UNKNOWN","NO_")): continue
            ir=(d.get("input_tokens")or 0);cr=(d.get("cache_read_tokens")or 0);cc=(d.get("cache_creation_tokens")or 0);op=(d.get("output_tokens")or 0)
            agg[t]=agg.get(t,0)+ir+cr*.1+cc*1.25+op*5
        except: pass
    return agg

c0=per_task_eff(f"{BASE}/logs/stable/ledger_C0_identity.jsonl")
LD=per_task_eff(f"{BASE}/logs/e4/ledger_LINEDEDUP_e4.jsonl")
G6=per_task_eff(f"{BASE}/logs/stable/ledger_GENTLE6K_stable.jsonl")

def delta_pct(c0d, md):
    common=sorted(set(c0d)&set(md)&set(feats))
    return {t: 100*(c0d[t]-md[t])/c0d[t] for t in common if c0d[t]>0}

ld_d=delta_pct(c0, LD); g6_d=delta_pct(c0, G6)

def boot_ci(xs,n=2000,seed=1):
    if len(xs)<3: return (None,None)
    random.seed(seed); ms=sorted(st.mean([random.choice(xs) for _ in xs]) for _ in range(n))
    return (round(ms[int(n*.025)],1),round(ms[int(n*.975)],1))

print("="*72)
print("PHASE 4A: CATE(cost) by dup_line_ratio bin — does redundancy predict LINEDEDUP benefit?")
print("="*72)
# bin tasks by dup_line_ratio
def binned(deltas, feat_key, bins):
    out=[]
    for lo,hi in bins:
        ts=[t for t in deltas if lo<=feats[t][feat_key]<hi]
        ds=[deltas[t] for t in ts]
        if ds: out.append((f"{lo}-{hi}",len(ds),round(st.mean(ds),1),boot_ci(ds)))
    return out
print("\nLINEDEDUP eff-cost saving by dup_line_ratio:")
for b,n,m,ci in binned(ld_d,"dup_line_ratio",[(0,0.18),(0.18,0.25),(0.25,0.5)]):
    print(f"  dup_ratio {b}: mean saving {m:+.1f}% CI={ci} (n={n})")

print("\n" + "="*72)
print("PHASE 4B: NEGATIVE CONTROL — does dup_line_ratio predict the SAME for GENTLE6K?")
print("(GENTLE6K caps dumps, doesn't dedup. dup_ratio should predict LINEDEDUP MORE than GENTLE6K if causal.)")
print("="*72)
print("\nGENTLE6K eff-cost saving by dup_line_ratio:")
for b,n,m,ci in binned(g6_d,"dup_line_ratio",[(0,0.18),(0.18,0.25),(0.25,0.5)]):
    print(f"  dup_ratio {b}: mean saving {m:+.1f}% CI={ci} (n={n})")

# correlation (exploratory, labeled)
def spearman(deltas, fk):
    common=sorted(deltas)
    xs=[feats[t][fk] for t in common]; ys=[deltas[t] for t in common]
    rx=_rank(xs); ry=_rank(ys); n=len(xs)
    d2=sum((rx[i]-ry[i])**2 for i in range(n))
    return 1-6*d2/(n*(n*n-1)) if n>2 else None
def _rank(v):
    idx=sorted(range(len(v)),key=lambda i:v[i]); r=[0]*len(v)
    for rank,i in enumerate(idx): r[i]=rank
    return r
print("\n=== EXPLORATORY rank-correlations (NOT causal) ===")
for fk in ["dup_line_ratio","largest_obs_chars","baseline_tokens_sent","n_observations"]:
    print(f"  spearman(LINEDEDUP saving, {fk}) = {spearman(ld_d,fk):+.2f}  |  GENTLE6K = {spearman(g6_d,fk):+.2f}")

out={"ld_delta":ld_d,"g6_delta":g6_d,
     "ld_by_dup":binned(ld_d,"dup_line_ratio",[(0,0.18),(0.18,0.25),(0.25,0.5)]),
     "g6_by_dup":binned(g6_d,"dup_line_ratio",[(0,0.18),(0.18,0.25),(0.25,0.5)])}
json.dump(out, open(f"{BASE}/results/pruning_ab/hte_estimates.json","w"), indent=1, default=str)
print("\nhte_estimates.json written")
