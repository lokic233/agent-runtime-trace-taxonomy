#!/usr/bin/env python3
"""aggregate_per_task.py — Section 13.1 per-task mapping across solver models.
Workload is task-level (cross-model stable); waste is per-solver. Writes mappings/per_task_l1_l2.jsonl."""
from __future__ import annotations
import json, sys, os, collections

def aggregate(adjudicated_records, index_rows):
    """adjudicated: trace_id -> adjudicated label set. index_rows: trace metadata+outcome+features."""
    by_task=collections.defaultdict(lambda: {"solvers":{}})
    idx={r["trace_id"]:r for r in index_rows}
    for tid, adj in adjudicated_records.items():
        meta=idx.get(tid)
        if not meta: continue
        task=meta["task_id"]; repo=meta["repo"]; solver=meta["solver_alias"]
        by_task[task]["repo"]=repo
        wl=adj.get("auto_merge",{}).get("workload_primary_l1") or adj.get("workload_primary_l1")
        by_task[task].setdefault("workload_votes",collections.Counter())[wl]+=1
        by_task[task]["solvers"][solver]={
            "outcome": ("SOLVED" if meta.get("resolved") else "UNSOLVED" if meta.get("resolved") is False else "ENV_FAILURE_OR_UNKNOWN"),
            "waste_l2": adj.get("auto_merge",{}).get("waste_l2_labels",[]),
            "primary_bottleneck": adj.get("auto_merge",{}).get("primary_bottleneck"),
            "total_tokens": meta.get("features",{}).get("total_tokens"),
            "trace_length": meta.get("n_events"),
        }
    out=[]
    for task, d in by_task.items():
        wv=d.get("workload_votes",collections.Counter())
        primary=wv.most_common(1)[0][0] if wv else None
        nsolv=len(d["solvers"])
        stability = "STABLE" if (wv and wv.most_common(1)[0][1]==sum(wv.values()) and nsolv>=2) else ("MIXED" if nsolv>=2 else "INSUFFICIENT")
        # cross-model waste comparison
        all_waste=[set(s["waste_l2"]) for s in d["solvers"].values()]
        shared=set.intersection(*all_waste) if all_waste else set()
        solver_specific={sv:sorted(set(s["waste_l2"])-shared) for sv,s in d["solvers"].items()}
        out.append({
            "task_id":task,"repo":d.get("repo"),
            "workload":{"primary_l1":primary,"l2_attributes":[],
                        "cross_model_stability":stability,"supporting_solver_count":nsolv},
            "per_solver_execution":[{"solver_alias":sv,**s} for sv,s in d["solvers"].items()],
            "cross_model_comparison":{"shared_waste_labels":sorted(shared),
                "solver_specific_labels":solver_specific,
                "capability_sensitive_patterns":[],"notes":""},
        })
    return out

if __name__=="__main__":
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--adjudicated", required=True); ap.add_argument("--index", required=True)
    ap.add_argument("--out", default="mappings/per_task_l1_l2.jsonl")
    a=ap.parse_args()
    adj_list=json.load(open(a.adjudicated))
    adj={r["trace_id"]:r for r in adj_list if "trace_id" in r}
    idx=[json.loads(l) for l in open(a.index)]
    res=aggregate(adj, idx)
    with open(a.out,"w") as f:
        for r in res: f.write(json.dumps(r,default=str)+"\n")
    print(f"per-task mapping: {len(res)} tasks -> {a.out}")
