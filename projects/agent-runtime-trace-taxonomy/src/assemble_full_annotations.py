#!/usr/bin/env python3
"""assemble_full_annotations.py — pair a1+a2 annotations per trace for each solver.

Reads annotations/raw_votes/full/<alias>/sNNN_{a1,a2}.json, parses robustly, aligns by
trace_id (derived from sample_id when absent), and emits per-solver paired records:
  annotations/raw_votes/full/<alias>/_paired.jsonl  (one line per trace: {trace_id, a1, a2})
Reports coverage: traces with 2 votes / 1 vote / 0 votes, and any trace_id mismatches.
"""
from __future__ import annotations
import sys, glob, json, os, re, collections
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from parse_annotator_output import extract_json

def tid_of(r, fallback_shard_tids=None, idx=None):
    if not isinstance(r, dict): return None
    t=r.get("trace_id")
    if t: return t
    sid=r.get("sample_id") or ""
    m=re.search(r'([\w.\-]+@solver_[A-Z])', sid)
    if m: return m.group(1)
    # last resort: task_id + alias
    task=r.get("task_id")
    if task and fallback_shard_tids:
        cand=[x for x in fallback_shard_tids if x.startswith(task+"@")]
        if len(cand)==1: return cand[0]
    return None

def assemble(alias, shard_dir, shard_src_dir):
    """shard_src_dir = /tmp/ann_shards/<alias> (the rendered inputs, to recover trace_ids by position)."""
    paired={}  # trace_id -> {a1, a2}
    stats=collections.Counter()
    nshards=len(glob.glob(f"{shard_dir}/s*_a1.json"))|len(glob.glob(f"{shard_dir}/s*_a2.json"))
    shard_ids=sorted({os.path.basename(f).split("_")[0] for f in glob.glob(f"{shard_dir}/s*.json")})
    for sid in shard_ids:
        # the rendered shard gives the authoritative trace_id ORDER for position fallback
        src=f"{shard_src_dir}/{sid}.json"
        shard_tids=[t["trace_id"] for t in json.load(open(src))] if os.path.exists(src) else []
        for role in ("a1","a2"):
            f=f"{shard_dir}/{sid}_{role}.json"
            if not (os.path.exists(f) and os.path.getsize(f)>20): continue
            d=extract_json(open(f).read())
            if not isinstance(d,list): stats[f"{role}_unparsed"]+=1; continue
            for i,r in enumerate(d):
                t=tid_of(r, shard_tids, i)
                if not t and i<len(shard_tids): t=shard_tids[i]  # positional fallback
                if not t: stats["no_tid"]+=1; continue
                paired.setdefault(t,{})[role]=r
    # coverage
    for t,v in paired.items():
        stats[f"have_{len(v)}_votes"]+=1
    out=f"{shard_dir}/_paired.jsonl"
    with open(out,"w") as fo:
        for t,v in paired.items():
            fo.write(json.dumps({"trace_id":t,"a1":v.get("a1"),"a2":v.get("a2")})+"\n")
    return dict(stats), len(paired), out

if __name__=="__main__":
    base="annotations/raw_votes/full"
    for alias in [d for d in ("solver_A","solver_B","solver_C","solver_G") if os.path.isdir(f"{base}/{d}")]:
        stats,n,out=assemble(alias, f"{base}/{alias}", f"/tmp/ann_shards/{alias}")
        print(f"{alias}: {n} traces paired -> {out}")
        print(f"   {stats}")
