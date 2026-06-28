#!/usr/bin/env python3
"""export_lora_dataset.py — Section 16 LoRA-ready exports.

16.1 SEMANTIC dataset (safe from annotation): input = task meta + deterministic features +
     compressed trace + generic capability tier + cutoff; target = workload/phase/waste/
     bottleneck/evidence-codes/intervention-hints/abstain. NO hidden CoT.
16.2 CONFIG-SELECTION dataset: SCHEMA/scaffold ONLY unless empirical config outcomes exist.
     recommended_config stays null / WEAK_ONLY; pareto_label_status=NOT_EMPIRICALLY_GROUNDED.
16.3 SPLIT: repo-based where possible; no task across train/test; no prefix/full of same trace
     across splits; held-out solver_E excluded from train; preserve model- & repo-transfer test.
"""
from __future__ import annotations
import json, sys, os, collections, hashlib, random

def make_semantic_example(meta, adj, compressed_trace, cutoff="FULL"):
    am=adj.get("auto_merge",{})
    return {
        "input":{
            "task_id":meta["task_id"],"repo":meta["repo"],
            "capability_tier":meta.get("capability_tier") or "UNK",  # GENERIC tier, never model name
            "cutoff":cutoff,
            "deterministic_features":{k:v for k,v in (meta.get("features") or {}).items() if k!="_null_reason"},
            "compressed_trace":compressed_trace,
        },
        "target":{
            "workload_l1":am.get("workload_primary_l1"),
            "waste_l2":am.get("waste_l2_labels",[]),
            "primary_bottleneck":am.get("primary_bottleneck"),
            "evidence_action_ids":am.get("evidence_action_ids",{}),
            "candidate_interventions":[],  # filled from waste->intervention map (weak)
            "abstain":adj.get("status")=="AMBIGUOUS",
        },
        "_provenance":{"taxonomy_version":"v1","label_source":"MULTI_MODEL_CONSENSUS",
                       "solver_alias":meta["solver_alias"]},
    }

def split_by_repo(metas, heldout_alias="solver_E", seed=20260628):
    """Repo-disjoint split + held-out solver excluded from train + model/repo transfer tests."""
    rng=random.Random(seed)
    repos=sorted({m["repo"] for m in metas if m["repo"]})
    rng.shuffle(repos)
    n=len(repos)
    test_repos=set(repos[:max(1,n//5)])           # ~20% repos -> repo-transfer test
    val_repos=set(repos[n//5:n//5+max(1,n//10)])
    train_repos=set(repos)-test_repos-val_repos
    split={"train":[],"validation":[],"test":[],"model_transfer_test":[],"repo_transfer_test":[]}
    for m in metas:
        tid=m["trace_id"]
        if m["solver_alias"]==heldout_alias:
            split["model_transfer_test"].append(tid)   # held-out solver NEVER in train
            continue
        if m["repo"] in test_repos: split["test"].append(tid); split["repo_transfer_test"].append(tid)
        elif m["repo"] in val_repos: split["validation"].append(tid)
        else: split["train"].append(tid)
    return split

def policy_scaffold():
    """16.2: empty/partial config-selection scaffold — NO empirical outcomes yet."""
    return {"_status":"SCAFFOLD_ONLY","pareto_label_status":"NOT_EMPIRICALLY_GROUNDED",
            "recommended_config":None,"note":"populate only from config_outcome.schema.json paired outcomes"}

if __name__=="__main__":
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--adjudicated"); ap.add_argument("--index"); ap.add_argument("--outdir",default="exports")
    ap.add_argument("--splitout", default="manifests/dataset_split.json")
    a=ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    if not (a.adjudicated and a.index and os.path.exists(a.adjudicated)):
        # scaffold mode (pre-annotation): write empty/headers + policy scaffold
        for s in ("lora_semantic_train","lora_semantic_validation","lora_semantic_test"):
            open(os.path.join(a.outdir,f"{s}.jsonl"),"w").close()
        json.dump(policy_scaffold(), open(os.path.join(a.outdir,"lora_policy_train.jsonl"),"w"), indent=2)
        print("SCAFFOLD mode: empty semantic exports + policy scaffold written (no annotations yet).")
        sys.exit(0)
    adj={r["trace_id"]:r for r in json.load(open(a.adjudicated)) if "trace_id" in r}
    idx={json.loads(l)["trace_id"]:json.loads(l) for l in open(a.index)}
    metas=[idx[t] for t in adj if t in idx]
    split=split_by_repo(metas)
    json.dump(split, open(a.splitout,"w"), indent=2)
    setmap={}
    for s,ids in split.items():
        for t in ids: setmap.setdefault(t,s)
    buckets=collections.defaultdict(list)
    for t,adjr in adj.items():
        if t not in idx: continue
        which=setmap.get(t)
        if which in ("repo_transfer_test","model_transfer_test"): which_file="test"
        else: which_file=which
        if not which_file: continue
        ex=make_semantic_example(idx[t], adjr, compressed_trace=f"<{idx[t]['n_events']} events>")
        buckets[which_file].append(ex)
    for s in ("train","validation","test"):
        with open(os.path.join(a.outdir,f"lora_semantic_{s}.jsonl"),"w") as f:
            for ex in buckets.get(s,[]): f.write(json.dumps(ex,default=str)+"\n")
    json.dump(policy_scaffold(), open(os.path.join(a.outdir,"lora_policy_train.jsonl"),"w"), indent=2)
    print(f"semantic export: train={len(buckets['train'])} val={len(buckets['validation'])} test={len(buckets['test'])}")
    print(f"split -> {a.splitout}; policy = SCAFFOLD (NOT_EMPIRICALLY_GROUNDED)")
