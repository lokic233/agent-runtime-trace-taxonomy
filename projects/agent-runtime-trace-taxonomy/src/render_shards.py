#!/usr/bin/env python3
"""Render blinded annotation shards for a solver (no LLM). Resumable; writes /tmp/ann_shards/<alias>/sNNN.json"""
import json, os, sys, math
sys.path.insert(0,'src')
from render_trace import render
def main(alias, index, shard_size=12, outdir=None):
    rows=[json.loads(l) for l in open(index) if json.loads(l)["solver_alias"]==alias]
    outdir=outdir or f"/tmp/ann_shards/{alias}"; os.makedirs(outdir,exist_ok=True)
    tids=[r["trace_id"] for r in rows]
    shards=[tids[i:i+shard_size] for i in range(0,len(tids),shard_size)]
    nrendered=0; nleak=0
    for si,shard in enumerate(shards):
        sf=f"{outdir}/s{si:03d}.json"
        if os.path.exists(sf): continue
        batch=[]
        for tid in shard:
            try: batch.append(render(tid, alias, "FULL", max_obs_chars=700, max_act_chars=450))
            except AssertionError: nleak+=1
            except Exception: pass
        json.dump(batch, open(sf,"w")); nrendered+=len(batch)
    print(f"{alias}: {len(shards)} shards, {nrendered} traces rendered, {nleak} blinding-skipped")
    return len(shards)
if __name__=="__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv)>3 else 12)
