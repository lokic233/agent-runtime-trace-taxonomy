#!/usr/bin/env python3
"""Phase C analysis — cache-tax mechanism transport (Sonnet 4.6, Haiku 4.5).
Primary estimand: cache_creation_fraction = cache_creation/(cache_creation+cache_read), per (model,arm).
Required contrast: C0 ~ SHAM << HYBRID1 (prefix rewriting busts the cache). Paired bootstrap CIs per task.
Reads ledgers from /data/users/dengcchi/prune_ab/logs/xmodel_phaseC/. stdlib only.
Output: results/pruning_ab/generalization/cache_tax_transport.json
"""
import json, os, glob, random, statistics
from collections import defaultdict
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from ledger_util import load_ledger_dedup

LOGDIR=os.environ.get("PHASEC_LOGS","/data/users/dengcchi/prune_ab/logs/xmodel_phaseC")
OUT=os.environ.get("PHASEC_OUT","/home/dengcchi/agent-runtime-trace-taxonomy/projects/agent-runtime-trace-taxonomy/results/pruning_ab/generalization/cache_tax_transport.json")
ANCHOR={"C0_identity":0.077,"SHAM":0.066,"HYBRID1_m7_agg2":0.784}  # opus-4.7 frozen (mechanism_effects.json)

def load_cells():
    cells=defaultdict(list)  # (model,arm) -> rows
    for p in glob.glob(os.path.join(LOGDIR,"ledger_*_rep*.jsonl")):
        b=os.path.basename(p)[len("ledger_"):-len(".jsonl")]
        # <model>_<arm>_rep<r>; arm may contain underscores -> split known model keys
        for mk in ("sonnet46","haiku45","opus47"):
            if b.startswith(mk+"_"):
                rest=b[len(mk)+1:]; arm=rest.rsplit("_rep",1)[0]
                cells[(mk,arm)].extend(load_ledger_dedup(p))
                break
    return cells

def cc_fraction(rows):
    cc=sum(r.get("cache_creation_tokens") or 0 for r in rows)
    cr=sum(r.get("cache_read_tokens") or 0 for r in rows)
    return (cc/(cc+cr)) if (cc+cr)>0 else None

def per_task_cc(rows):
    by=defaultdict(lambda:[0,0])  # task -> [cc,cr]
    for r in rows:
        t=r.get("task_id"); by[t][0]+=r.get("cache_creation_tokens") or 0; by[t][1]+=r.get("cache_read_tokens") or 0
    return {t:(cc/(cc+cr) if (cc+cr)>0 else None) for t,(cc,cr) in by.items()}

def bootstrap_ci(vals, n=2000, seed=42):
    vals=[v for v in vals if v is not None]
    if len(vals)<2: return [None,None]
    random.seed(seed); means=[]
    for _ in range(n):
        s=[random.choice(vals) for _ in vals]; means.append(sum(s)/len(s))
    means.sort(); return [round(means[int(0.025*n)],4), round(means[int(0.975*n)],4)]

def main():
    cells=load_cells()
    out={"estimand":"cache_creation_fraction = cache_creation/(cache_creation+cache_read)",
         "opus_anchor_frozen":ANCHOR,"contrast":"C0 ~ SHAM << HYBRID1 (prefix rewriting busts cache)",
         "cells":{}, "by_model":{}}
    for (mk,arm),rows in sorted(cells.items()):
        pt=per_task_cc(rows)
        out["cells"][f"{mk}/{arm}"]={"n_calls":len(rows),"n_tasks":len(pt),
            "cc_fraction_pooled":round(cc_fraction(rows),4) if cc_fraction(rows) is not None else None,
            "cc_fraction_per_task_mean":round(statistics.mean([v for v in pt.values() if v is not None]),4) if any(v is not None for v in pt.values()) else None,
            "cc_fraction_ci":bootstrap_ci(list(pt.values()))}
    # per-model mechanism verdict: is HYBRID1 cc_fraction >> C0 and SHAM (non-overlapping CIs)?
    for mk in ("sonnet46","haiku45","opus47"):
        c0=out["cells"].get(f"{mk}/C0_identity"); sham=out["cells"].get(f"{mk}/SHAM"); hyb=out["cells"].get(f"{mk}/HYBRID1_m7_agg2")
        if c0 and hyb:
            verdict="SUPPORTED" if (hyb["cc_fraction_ci"][0] and c0["cc_fraction_ci"][1] and hyb["cc_fraction_ci"][0]>c0["cc_fraction_ci"][1]) else "NOT_SEPARATED/UNDERPOWERED"
            out["by_model"][mk]={"C0":c0["cc_fraction_pooled"],"SHAM":sham["cc_fraction_pooled"] if sham else None,
                                 "HYBRID1":hyb["cc_fraction_pooled"],"cache_tax_verdict":verdict}
    os.makedirs(os.path.dirname(OUT),exist_ok=True)
    json.dump(out, open(OUT,"w"), indent=1)
    print(json.dumps(out["by_model"], indent=1)); print("wrote", OUT)

if __name__=="__main__": main()
