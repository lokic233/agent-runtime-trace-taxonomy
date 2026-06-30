#!/usr/bin/env python3
"""Phase 3: extract PRE-TREATMENT features from C0 baseline trajectories only.
Decision point = before any pruning. Features use ONLY the C0 trace (the observed pre-intervention world)."""
import json, os, glob, hashlib, statistics as st
BASE="/data/users/dengcchi/prune_ab"
G=set(json.load(open("/tmp/golden50.json")))

def obs_texts(history):
    out=[]
    for m in history:
        if m.get("role")=="tool" or (m.get("role")=="user" and m.get("message_type")=="observation"):
            c=m.get("content"); t=""
            if isinstance(c,list): t="".join(b.get("text","") for b in c if isinstance(b,dict))
            elif isinstance(c,str): t=c
            if t: out.append(t)
    return out

def extract(tid):
    # use the stable C0 traj (canonical baseline); fallback to full_C0
    cand=glob.glob(f"{BASE}/arms/stable_C0_identity/{tid}/*.traj") or glob.glob(f"{BASE}/arms/full_C0_identity/{tid}/*.traj")
    if not cand: return None
    try: d=json.load(open(cand[0]))
    except: return None
    h=d.get("history",[]); ms=d.get("info",{}).get("model_stats",{})
    obs=obs_texts(h)
    if not obs: return None
    all_lines=[]; 
    for o in obs: all_lines+= [l.strip() for l in o.split("\n") if len(l.strip())>=12]
    # redundancy: exact duplicate line ratio
    seen=set(); dup=0
    for l in all_lines:
        if l in seen: dup+=1
        else: seen.add(l)
    obs_sizes=sorted(len(o) for o in obs)
    # repeated whole-observation ratio
    ohashes=[hashlib.sha256(o.encode()).hexdigest() for o in obs]
    rep_obs=len(ohashes)-len(set(ohashes))
    f={
      "task_id":tid,
      "repo":tid.split("__")[0],
      # context volume
      "n_observations":len(obs),
      "total_obs_chars":sum(len(o) for o in obs),
      "largest_obs_chars":obs_sizes[-1],
      "median_obs_chars":obs_sizes[len(obs_sizes)//2],
      "p90_obs_chars":obs_sizes[int(len(obs_sizes)*0.9)] if len(obs_sizes)>1 else obs_sizes[-1],
      "baseline_calls":ms.get("api_calls",0),
      "baseline_tokens_sent":ms.get("tokens_sent",0),
      # redundancy (pre-treatment, from observed content)
      "dup_line_ratio":dup/max(len(all_lines),1),
      "n_dup_lines":dup,
      "repeated_obs_ratio":rep_obs/max(len(obs),1),
      # task characteristic
      "task_stmt_chars": len(obs_texts([h[1]])[0]) if len(h)>1 and h[1].get("role")=="user" else 0,
    }
    return f
rows=[extract(t) for t in sorted(G)]
rows=[r for r in rows if r]
# write as jsonl (no parquet dep guaranteed)
with open(f"{BASE}/results/pruning_ab/pre_treatment_features.jsonl","w") as fo:
    for r in rows: fo.write(json.dumps(r)+"\n")
print(f"extracted pre-treatment features for {len(rows)}/{len(G)} tasks")
print(f"feature keys: {sorted(rows[0].keys())}")
# show distribution of the key features
import statistics as st
for k in ["n_observations","dup_line_ratio","largest_obs_chars","baseline_calls","baseline_tokens_sent"]:
    vals=[r[k] for r in rows]
    print(f"  {k:22s} min={min(vals):.2f} median={st.median(vals):.2f} max={max(vals):.2f}")
