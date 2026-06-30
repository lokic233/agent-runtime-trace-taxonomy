#!/usr/bin/env python3
"""Phase 2: mechanism-level causal tests. Cache tax (prefix stability) + intelligence tax (info novelty)."""
import json, os, glob, statistics as st, math
BASE="/data/users/dengcchi/prune_ab"
G=set(json.load(open("/tmp/golden50.json")))
INT10=set(json.load(open("/tmp/interesting10.json")))

def boot_ci(xs, n=2000, seed=0):
    import random; random.seed(seed)
    if len(xs)<3: return (None,None)
    ms=sorted(st.mean([random.choice(xs) for _ in xs]) for _ in range(n))
    return (round(ms[int(n*.025)],3), round(ms[int(n*.975)],3))

def ledger_cache(path, tasks=None):
    """per-task cache_read, cache_creation, eff cost, calls."""
    if not os.path.exists(path): return {}
    agg={}
    for l in open(path):
        try:
            d=json.loads(l); t=d.get("task_id")
            if not t or str(t).startswith(("UNKNOWN","NO_")): continue
            if tasks and t not in tasks: continue
            ir=(d.get("input_tokens")or 0);cr=(d.get("cache_read_tokens")or 0);cc=(d.get("cache_creation_tokens")or 0);op=(d.get("output_tokens")or 0)
            a=agg.setdefault(t,{"cr":0,"cc":0,"eff":0.,"out":0,"calls":0})
            a["cr"]+=cr;a["cc"]+=cc;a["eff"]+=ir+cr*.1+cc*1.25+op*5;a["out"]+=op;a["calls"]+=1
        except: pass
    return agg

print("="*70)
print("MECHANISM A: CACHE TAX — does prefix rewriting raise cache_creation share?")
print("="*70)
# Compare cache_creation FRACTION across methods (prefix-stable vs prefix-rewriting)
# Treatment contrast: SHAM (byte-identical, prefix-stable) vs HYBRID1 (recency-rewrite) vs LINEDEDUP (content-stable)
# Use A/A reps where all 3 exist (10 interesting tasks), pooled per method.
def cc_fraction_aa(method):
    """cache_creation / (cache_read+cache_creation) pooled across reps, A/A 10 tasks."""
    fracs=[]
    for r in range(1,6):
        f=f"{BASE}/logs/phase34/ledger_{method}_rep{r}.jsonl"
        agg=ledger_cache(f, INT10)
        for t,v in agg.items():
            tot=v["cr"]+v["cc"]
            if tot>1000: fracs.append(v["cc"]/tot)
    return fracs
for m in ["C0_identity","SHAM","HYBRID1_m7_agg2"]:
    fr=cc_fraction_aa(m)
    if fr:
        ci=boot_ci(fr)
        print(f"  {m:18s} cache_creation_fraction: mean={st.mean(fr):.3f} CI={ci} (n={len(fr)} task-reps)")
print("\n  INTERPRETATION: C0/SHAM should have LOW cc-fraction (stable prefix, mostly cache_read).")
print("  HYBRID1 should have HIGH cc-fraction (rewrites prefix -> re-creates cache).")
print("  SHAM is the key control: same code path as a pruner but byte-identical output ->")
print("  if SHAM stays low like C0, the cc-fraction jump in HYBRID1 is CAUSED by prefix rewriting, not the shim.")

mech_out={"cache_tax":{}}
for m in ["C0_identity","SHAM","HYBRID1_m7_agg2"]:
    fr=cc_fraction_aa(m)
    if fr: mech_out["cache_tax"][m]={"cc_fraction_mean":round(st.mean(fr),3),"ci":boot_ci(fr),"n":len(fr)}
json.dump(mech_out, open(f"{BASE}/results/pruning_ab/mechanism_effects.json","w"), indent=1, default=str)
print("\nmechanism_effects.json (cache tax) written")
