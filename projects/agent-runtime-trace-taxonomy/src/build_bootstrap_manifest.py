#!/usr/bin/env python3
"""build_bootstrap_manifest.py — Stage A1 diversity-maximizing bootstrap sample.

Select ~60-80 traces from TAXONOMY-DEVELOPMENT models only (held_out excluded) for
open coding. Stratify across the Section-6 axes so open coders see the full behavioral
range, not just the common case. Outcome (resolved) is used for BALANCE ONLY and is
written to the manifest under a `_sampling_only` block that the open-coding harness
strips before showing a coder.

Strata axes (derived from deterministic features):
  - outcome: solved / unsolved
  - token use: low/med/high (tertiles within available-token traces; null bucket too)
  - trajectory length: short/med/long (event-count tertiles)
  - behavior mix: search-heavy / edit-heavy / test-heavy / balanced
  - tool-result error: low / high (error-rate median split)
  - stagnation: none / present (longest_no_new_evidence_streak tertile)
  - repo diversity, task diversity (greedy spread)
Deterministic: fixed seed; reproducible.
"""
from __future__ import annotations
import json, sys, os, collections, random, statistics as st
sys.path.insert(0, os.path.dirname(__file__))

SEED = 20260628
TARGET_MIN, TARGET_MAX = 60, 80
PER_SOLVER_TARGET = 18  # ~15-20 per included dev solver

def tertile_bucket(x, lo, hi):
    if x is None: return "na"
    if x <= lo: return "low"
    if x >= hi: return "high"
    return "med"

def behavior_mix(f):
    s=f["search_call_count"]; e=f["patch_attempts"]; t=f["targeted_test_count"]
    tot=s+e+t
    if tot==0: return "other"
    mx=max(s,e,t)
    if mx==s and s>=max(e,t): return "search_heavy"
    if mx==e and e>=max(s,t): return "edit_heavy"
    if mx==t and t>=max(s,e): return "test_heavy"
    return "balanced"

def stratum_key(r):
    f=r["features"]
    return (
        "solved" if r["resolved"] else ("unsolved" if r["resolved"] is False else "unk"),
        r["_tok_b"], r["_len_b"], behavior_mix(f),
        "errhi" if (f.get("tool_error_rate") or 0) > r["_err_med"] else "errlo",
        "stag" if (f.get("longest_no_new_evidence_streak") or 0) >= r["_stag_hi"] else "nostag",
    )

def build(index_rows, dev_aliases):
    rng = random.Random(SEED)
    dev = [r for r in index_rows if r["solver_alias"] in dev_aliases and not r["held_out"]]
    if not dev:
        return [], {"error":"no dev traces"}
    # compute global thresholds per solver-pooled
    toks=[r["features"]["total_tokens"] for r in dev if r["features"]["total_tokens"]]
    lens=[r["n_events"] for r in dev]
    errs=[r["features"]["tool_error_rate"] for r in dev if r["features"]["tool_error_rate"] is not None]
    stags=[r["features"]["longest_no_new_evidence_streak"] or 0 for r in dev]
    tok_lo,tok_hi=(st.quantiles(toks,n=3) if len(toks)>=3 else (None,None))
    len_lo,len_hi=st.quantiles(lens,n=3)[0], st.quantiles(lens,n=3)[1]
    err_med=st.median(errs) if errs else 0.0
    stag_hi=st.quantiles(stags,n=3)[1] if len(stags)>=3 else 1
    for r in dev:
        f=r["features"]
        r["_tok_b"]=tertile_bucket(f["total_tokens"], tok_lo, tok_hi) if tok_lo is not None else "na"
        r["_len_b"]=tertile_bucket(r["n_events"], len_lo, len_hi)
        r["_err_med"]=err_med; r["_stag_hi"]=stag_hi
    # group by stratum, then round-robin pick to maximize coverage, balancing per-solver
    strata=collections.defaultdict(list)
    for r in dev: strata[stratum_key(r)].append(r)
    for k in strata: rng.shuffle(strata[k])
    # greedy: iterate strata in size-ascending order (rare strata first), pick 1 each round
    picked=[]; per_solver=collections.Counter(); seen_tasks=set()
    stratum_order=sorted(strata.keys(), key=lambda k:len(strata[k]))
    target = min(TARGET_MAX, max(TARGET_MIN, PER_SOLVER_TARGET*len(dev_aliases)))
    while len(picked) < target:
        progressed=False
        for k in stratum_order:
            if len(picked) >= target: break
            bucket=strata[k]
            # pick the next trace in this stratum that keeps solver balance + task diversity
            for i,r in enumerate(bucket):
                if r is None: continue
                if per_solver[r["solver_alias"]] >= PER_SOLVER_TARGET+4: continue
                # prefer unseen task (diversity) but allow dup task across solvers
                picked.append(r); per_solver[r["solver_alias"]]+=1; seen_tasks.add(r["task_id"])
                bucket[i]=None; progressed=True
                break
        if not progressed: break
    return picked, {
        "target":target,"dev_aliases":dev_aliases,
        "thresholds":{"tok_tertiles":[tok_lo,tok_hi],"len_tertiles":[len_lo,len_hi],
                      "err_median":err_med,"stag_hi":stag_hi},
        "n_strata":len(strata),"per_solver":dict(per_solver),
    }

def to_manifest_record(r):
    f=r["features"]
    return {
        "sample_id": "BOOT-"+r["trace_id"],
        "trace_id": r["trace_id"], "task_id": r["task_id"], "repo": r["repo"],
        "solver_alias": r["solver_alias"], "capability_tier": r["capability_tier"],
        "source_path": r["source_path"], "source_node": "devvm14382",
        "n_events": r["n_events"],
        # deterministic features are SHOWN to open coders (evidence) — outcome is NOT
        "deterministic_features": {k:v for k,v in f.items() if k!="_null_reason"},
        "_sampling_only": {   # STRIPPED before an open coder sees the record
            "resolved": r["resolved"],
            "stratum": list(stratum_key(r)),
        },
    }

if __name__=="__main__":
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--index", default="/tmp/trace_index.jsonl")
    ap.add_argument("--dev", default="solver_A,solver_B,solver_C")  # solver_D(8B) absent; solver_E held out
    ap.add_argument("--out", required=True)
    ap.add_argument("--balance-out", default=None)
    a=ap.parse_args()
    rows=[json.loads(l) for l in open(a.index)]
    dev=a.dev.split(",")
    picked,meta=build(rows, dev)
    with open(a.out,"w") as fo:
        for r in picked: fo.write(json.dumps(to_manifest_record(r))+"\n")
    print(f"selected {len(picked)} bootstrap traces -> {a.out}")
    print("meta:", json.dumps(meta, default=str)[:400])
    if a.balance_out:
        json.dump({"picked":len(picked),"meta":meta,
                   "by_solver":dict(collections.Counter(r["solver_alias"] for r in picked)),
                   "by_outcome":dict(collections.Counter(("solved" if r["resolved"] else "unsolved" if r["resolved"] is False else "unk") for r in picked)),
                   "by_behavior":dict(collections.Counter(behavior_mix(r["features"]) for r in picked)),
                   "by_repo":dict(collections.Counter(r["repo"] for r in picked)),
                   }, open(a.balance_out,"w"), indent=2, default=str)
        print("balance ->", a.balance_out)
