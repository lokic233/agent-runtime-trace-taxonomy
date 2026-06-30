#!/usr/bin/env python3
"""Phase 1: action-opportunity event sampler. Enumerates ALL candidate events per C0 trajectory,
assigns to strata (exact redundancy/repeated-read/large-output/active/hard-negative/superseded).
Targets 300-500 balanced events across strata."""
import json, os, glob, hashlib
BASE="/data/users/dengcchi/prune_ab"
G=sorted(json.load(open("/tmp/golden50.json")))

def obs_from_traj(traj_path):
    """extract (index, text, metadata) for each tool observation."""
    try: h=json.load(open(traj_path))["history"]
    except: return []
    obs=[]
    for i,m in enumerate(h):
        if m.get("role")!="tool": continue
        c=m.get("content")
        if isinstance(c,list): t="".join(b.get("text","") for b in c if isinstance(b,dict))
        elif isinstance(c,str): t=c
        else: continue
        if len(t)<200: continue  # skip trivial
        obs.append({"idx":i,"text":t,"chars":len(t),"lines":t.count("\n")+1})
    return obs

def strata_for_obs(obs_list, obs_idx):
    """classify an observation relative to prior context."""
    target=obs_list[obs_idx]
    prior=obs_list[:obs_idx]
    strata=[]
    # compute line-level redundancy vs prior
    t_lines=[l.strip() for l in target["text"].split("\n") if len(l.strip())>=12]
    prior_lines=set()
    for p in prior:
        for l in p["text"].split("\n"):
            if len(l.strip())>=12: prior_lines.add(l.strip())
    if t_lines:
        dup_count=sum(1 for l in t_lines if l in prior_lines)
        dup_frac=dup_count/len(t_lines)
    else: dup_count=0; dup_frac=0
    # Stratum A: exact redundancy (>40% lines duplicated)
    if dup_frac>0.4 and dup_count>=5:
        strata.append("A_exact_redundancy")
    # Stratum B: repeated file read (same first line = file path header, appeared before)
    first_line=target["text"].split("\n")[0].strip()
    for p in prior:
        if p["text"].split("\n")[0].strip()==first_line and len(first_line)>20:
            strata.append("B_repeated_file_read"); break
    # Stratum C: large recoverable output (>4000 chars, tool output)
    if target["chars"]>4000:
        strata.append("C_large_output")
    # Stratum E: active dependency (low dup = novel content, likely active)
    if dup_frac<0.1 and target["chars"]>1000:
        strata.append("E_active_dependency")
    # Stratum F: hard negative (some dup but also unique delta — >20% dup but <80%)
    if 0.2<dup_frac<0.8 and dup_count>=3:
        strata.append("F_hard_negative")
    # Stratum D: superseded (a prior obs has same file header AND this one is newer)
    if "B_repeated_file_read" in strata and dup_frac>0.5:
        strata.append("D_superseded_state")
    if not strata:
        strata.append("H_control")  # natural-noise control (ordinary, no clear pattern)
    return strata, {"dup_lines":dup_count,"dup_frac":round(dup_frac,2),"total_lines":len(t_lines)}

events=[]
for t in G:
    cand=glob.glob(f"{BASE}/arms/stable_C0_identity/{t}/*.traj")
    if not cand: continue
    obs=obs_from_traj(cand[0])
    for oi in range(1, len(obs)):  # skip first obs (task stmt)
        o=obs[oi]; strata, meta=strata_for_obs(obs, oi)
        events.append({
            "event_id":f"{t}#call{o['idx']}",
            "task_id":t,"repo":t.split("__")[0],"run_id":"stable_C0",
            "call_id":o["idx"],"observation_id":f"obs{oi}",
            "strata":strata,
            "segment_size_chars":o["chars"],"segment_size_tokens":o["chars"]//4,
            "segment_text_hash":hashlib.sha256(o["text"][:2000].encode()).hexdigest()[:12],
            "eligibility_metadata":meta,
            "available_actions":["NO_OP","LINE_DEDUP","GENTLE_CAP","RETRIEVABLE_REFERENCE"],
            "data_complete":True,
        })
with open(f"{BASE}/results/pruning_ab/candidate_events.jsonl","w") as fo:
    for e in events: fo.write(json.dumps(e)+"\n")
from collections import Counter
sc=Counter()
for e in events:
    for s in e["strata"]: sc[s]+=1
print(f"total candidate events: {len(events)}")
print("stratum distribution:")
for s,c in sc.most_common(): print(f"  {s}: {c}")
print(f"\ntasks covered: {len(set(e['task_id'] for e in events))}")
