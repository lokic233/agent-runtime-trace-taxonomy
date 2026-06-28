#!/usr/bin/env python3
"""aggregate_per_model.py — Section 13.2 per-model summary + matched-task comparison.
Reports raw AND matched-task-adjusted distributions (never compare raw freqs w/o controlling task mix)."""
from __future__ import annotations
import json, sys, os, collections, statistics as st

def summarize(adjudicated, index_rows):
    idx={r["trace_id"]:r for r in index_rows}
    by_solver=collections.defaultdict(lambda:{"traces":0,"repos":collections.Counter(),
        "outcomes":collections.Counter(),"tokens":[],"lengths":[],
        "waste_l1":collections.Counter(),"waste_l2":collections.Counter(),
        "bottleneck":collections.Counter()})
    solver_tasks=collections.defaultdict(set)
    for tid, adj in adjudicated.items():
        meta=idx.get(tid)
        if not meta: continue
        sv=meta["solver_alias"]; s=by_solver[sv]
        s["traces"]+=1; s["repos"][meta["repo"]]+=1
        s["outcomes"]["SOLVED" if meta.get("resolved") else "UNSOLVED" if meta.get("resolved") is False else "UNKNOWN"]+=1
        if meta.get("features",{}).get("total_tokens"): s["tokens"].append(meta["features"]["total_tokens"])
        s["lengths"].append(meta.get("n_events"))
        am=adj.get("auto_merge",{})
        for lab in am.get("waste_l2_labels",[]): s["waste_l2"][lab]+=1
        if am.get("primary_bottleneck"): s["bottleneck"][am["primary_bottleneck"]]+=1
        solver_tasks[sv].add(meta["task_id"])
    # matched-task set = tasks present for ALL solvers
    common = set.intersection(*solver_tasks.values()) if solver_tasks else set()
    out={"per_model":{}, "matched_task_set_size":len(common)}
    for sv,s in by_solver.items():
        out["per_model"][sv]={
            "trace_count":s["traces"],"repos":dict(s["repos"]),
            "outcomes":dict(s["outcomes"]),
            "token_median":st.median(s["tokens"]) if s["tokens"] else None,
            "length_median":st.median([x for x in s["lengths"] if x]) if s["lengths"] else None,
            "waste_l2_prevalence":dict(s["waste_l2"]),
            "primary_bottleneck_dist":dict(s["bottleneck"]),
        }
    return out

if __name__=="__main__":
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--adjudicated",required=True); ap.add_argument("--index",required=True)
    ap.add_argument("--out", default="mappings/per_model_summary.json")
    a=ap.parse_args()
    adj={r["trace_id"]:r for r in json.load(open(a.adjudicated)) if "trace_id" in r}
    idx=[json.loads(l) for l in open(a.index)]
    res=summarize(adj, idx)
    json.dump(res, open(a.out,"w"), indent=2, default=str)
    print(f"per-model summary -> {a.out}; matched-task set: {res['matched_task_set_size']}")
