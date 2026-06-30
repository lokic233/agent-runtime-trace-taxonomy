#!/usr/bin/env python3
"""Build blind decision-point views for frontier annotation: prefix-only, candidate segment, no outcomes."""
import json, os, glob, hashlib
BASE="/data/users/dengcchi/prune_ab"
G=sorted(json.load(open("/tmp/golden50.json")))

def obs_texts_indexed(history):
    out=[]
    for i,m in enumerate(history):
        if m.get("role")=="tool" or (m.get("role")=="user" and m.get("message_type")=="observation"):
            c=m.get("content");t=""
            if isinstance(c,list): t="".join(b.get("text","") for b in c if isinstance(b,dict))
            elif isinstance(c,str): t=c
            if t: out.append((i,t))
    return out

# select decision events: for a sample of tasks, pick the call with the largest observation as the candidate
# (eligible = >=2000 chars). Build prefix = everything up to & including that obs.
events=[]
import random; random.seed(7)
sample=G  # all 50 tasks, 1 decision event each (the largest-obs call) for tractable annotation
for t in sample:
    cand=glob.glob(f"{BASE}/arms/stable_C0_identity/{t}/*.traj")
    if not cand: continue
    try: d=json.load(open(cand[0]))
    except: continue
    h=d.get("history",[]); obs=obs_texts_indexed(h)
    if not obs: continue
    # candidate = largest observation
    cidx,ctext=max(obs,key=lambda x:len(x[1]))
    if len(ctext)<2000: continue
    # prefix = task statement + brief summary of prior obs (truncated for annotation tractability)
    task_stmt=""
    for m in h[:3]:
        if m.get("role")=="user":
            c=m.get("content"); task_stmt=(c if isinstance(c,str) else " ".join(x.get("text","") for x in c if isinstance(x,dict)))[:1500]; break
    prior_obs=[(i,len(x)) for i,x in obs if i<cidx]
    # candidate segment features (prefix-state)
    lines=ctext.split("\n")
    # does each line have an earlier copy in prior obs?
    prior_lines=set()
    for i,x in obs:
        if i<cidx:
            for l in x.split("\n"):
                if len(l.strip())>=12: prior_lines.add(l.strip())
    dup_lines=sum(1 for l in lines if l.strip() in prior_lines and len(l.strip())>=12)
    events.append({
        "event_id": f"{t}#call{cidx}",
        "task_id": t, "repo": t.split("__")[0],
        "decision_call_obs_index": cidx,
        "task_statement_excerpt": task_stmt,
        "n_prior_observations": len(prior_obs),
        "candidate_segment_chars": len(ctext),
        "candidate_segment_lines": len(lines),
        "candidate_dup_lines_vs_prior": dup_lines,
        "candidate_segment_text": ctext[:6000],  # truncated for annotation
        "candidate_segment_tail": ctext[-1000:] if len(ctext)>6000 else "",
        # NO outcome, NO future trajectory, NO action taken
    })
with open(f"{BASE}/results/pruning_ab/blind_decision_views.jsonl","w") as fo:
    for e in events: fo.write(json.dumps(e)+"\n")
print(f"blind decision views: {len(events)} events (1 per task, largest-obs call)")
print(f"sample event: {events[0]['event_id']} seg={events[0]['candidate_segment_chars']}c dup_lines={events[0]['candidate_dup_lines_vs_prior']}")
