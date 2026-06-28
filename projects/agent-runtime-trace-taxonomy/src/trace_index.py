#!/usr/bin/env python3
"""trace_index.py — discover + normalize + feature-extract + join resolve status.

Single source of truth for "what traces exist and what are their deterministic
properties". Reads config/trace_sources.yaml. The resolve status (outcome) is
loaded here for SAMPLING BALANCE ONLY and is firewalled downstream (open coders /
prefix views never receive it).

Blinding: maps real source -> solver_alias via private/model_alias_map.json IF present,
else falls back to the alias declared in trace_sources.yaml. The real model name is
NEVER attached to a normalized trace or a feature row.
"""
from __future__ import annotations
import json, glob, os, sys, hashlib
from typing import Optional
sys.path.insert(0, os.path.dirname(__file__))
from normalize_traces import normalize_trace, load_raw
from extract_deterministic_features import extract_features

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # project root

def _load_yaml(path):
    import yaml  # pyyaml present on these boxes
    with open(path) as f:
        return yaml.safe_load(f)

def load_resolved(report_path: str, instance_id: str) -> Optional[bool]:
    try:
        r = json.load(open(report_path))
    except Exception:
        return None
    if "resolved" in r:
        return bool(r["resolved"])
    if instance_id in r and isinstance(r[instance_id], dict):
        return bool(r[instance_id].get("resolved"))
    for v in r.values():
        if isinstance(v, dict) and "resolved" in v:
            return bool(v["resolved"])
    return None

def discover_traces(source: dict) -> list[dict]:
    """Return [{path, task_id}] for one trace_sources entry, layout-aware."""
    root = source["path"]; layout = source.get("layout")
    out = []
    if layout == "nested_traj_json":      # trajs/<inst>/<inst>.traj.json
        for fp in sorted(glob.glob(f"{root}/trajs/*/*.traj.json")):
            out.append({"path": fp, "task_id": os.path.basename(fp).replace(".traj.json","")})
    elif layout == "flat_traj":           # trajs/<inst>.traj
        for fp in sorted(glob.glob(f"{root}/trajs/*.traj")):
            out.append({"path": fp, "task_id": os.path.basename(fp).replace(".traj","")})
    elif layout == "openhands_flat":      # trajs/<inst>.json  (OpenHands messages format)
        for fp in sorted(glob.glob(f"{root}/trajs/*.json")):
            out.append({"path": fp, "task_id": os.path.basename(fp).replace(".json","")})
    elif layout == "nested_traj":         # <inst>/<inst>.traj  (live runs, no trajs/ wrapper)
        for fp in sorted(glob.glob(f"{root}/*/*.traj")):
            out.append({"path": fp, "task_id": os.path.basename(fp).replace(".traj","")})
    return out

def report_path_for(source: dict, task_id: str) -> Optional[str]:
    root = source["path"]
    for cand in (f"{root}/logs/{task_id}/report.json",):
        if os.path.exists(cand):
            return cand
    return None

def build_index(sources_yaml: str, aliases_json: Optional[str], only_status=("available","available_HELDOUT","generating","optional_generating"),
                limit_per_source: Optional[int]=None) -> list[dict]:
    cfg = _load_yaml(sources_yaml)["trace_sources"]
    tiers = {}
    if aliases_json and os.path.exists(aliases_json):
        am = json.load(open(aliases_json))
        tiers = (am.get("_capability_tier") or {}, am.get("_locality") or {})
    rows = []
    for key, src in cfg.items():
        if src.get("status") not in only_status:
            continue
        if not os.path.isdir(src["path"]):
            continue
        alias = src["alias"]
        tier = tiers[0].get(alias) if tiers else None
        loc = tiers[1].get(alias) if tiers else None
        traces = discover_traces(src)
        if limit_per_source: traces = traces[:limit_per_source]
        for t in traces:
            try:
                raw = load_raw(t["path"])
            except Exception:
                continue
            nt = normalize_trace(raw, trace_id=f"{t['task_id']}@{alias}", task_id=t["task_id"],
                                 solver_alias=alias, capability_tier=tier, locality=loc,
                                 source_path=t["path"])
            # join resolve status (sampling balance only)
            rp = report_path_for(src, t["task_id"])
            resolved = load_resolved(rp, t["task_id"]) if rp else None
            nt["outcome"]["resolved"] = resolved
            feats = extract_features(nt, model_stats=(raw.get("info",{}) or {}).get("model_stats"))
            repo = t["task_id"].split("__")[0] if "__" in t["task_id"] else None
            rows.append({
                "trace_id": nt["trace_id"], "task_id": t["task_id"], "repo": repo,
                "solver_alias": alias, "capability_tier": tier, "status_key": key,
                "held_out": src.get("status") == "available_HELDOUT",
                "resolved": resolved, "n_events": nt["n_events"], "source_path": t["path"],
                "features": feats,
            })
    return rows

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", default=os.path.join(HERE,"config","trace_sources.yaml"))
    ap.add_argument("--aliases", default=os.path.join(HERE,"private","model_alias_map.json"))
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    rows = build_index(a.sources, a.aliases, limit_per_source=a.limit)
    if a.out:
        with open(a.out,"w") as f:
            for r in rows: f.write(json.dumps(r)+"\n")
    import collections
    by_solver = collections.Counter(r["solver_alias"] for r in rows)
    by_res = collections.Counter((r["solver_alias"], r["resolved"]) for r in rows)
    print(f"indexed {len(rows)} traces")
    for s in sorted(by_solver):
        res=by_res[(s,True)]; un=by_res[(s,False)]; nn=by_res[(s,None)]
        print(f"  {s}: {by_solver[s]} traces (resolved={res}, unresolved={un}, unknown={nn})")
