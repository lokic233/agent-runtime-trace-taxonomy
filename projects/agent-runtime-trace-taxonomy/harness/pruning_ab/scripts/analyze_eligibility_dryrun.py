#!/usr/bin/env python3
"""Offline eligibility analyzer for the Study-2 dry run. Replays each *.traj and computes, at every
main-agent step, whether the NEWEST tool observation meets base availability
(seg_chars>=2000 AND dup_lines>=5 vs prior observations AND LINEDEDUP would remove >=1 line),
mirroring mrt_confirmatory_shim exactly. Reports per-task availability + dup_frac distribution.
No shim / no network. Usage: analyze_eligibility_dryrun.py <traj_dir> <out.json>
"""
import json, sys, glob, os, hashlib, collections

MIN_SEG=2000; MIN_DUP=5; MIN_LINE=12

def txt(content):
    if isinstance(content,str): return content
    if isinstance(content,list):
        parts=[]
        for b in content:
            if isinstance(b,dict):
                if isinstance(b.get("text"),str): parts.append(b["text"])
                elif b.get("type")=="tool_result":
                    inner=b.get("content")
                    if isinstance(inner,str): parts.append(inner)
                    elif isinstance(inner,list):
                        parts.append(" ".join(x.get("text","") for x in inner if isinstance(x,dict)))
        return "".join(parts)
    return str(content) if content else ""

def elig_lines(t): return [l.strip() for l in t.split("\n") if len(l.strip())>=MIN_LINE]

def is_obs(i,m):
    # traj-authoritative: message_type=='observation' marks a tool observation (role may be user OR tool);
    # skip the first user message (i<=1 = the task prompt / initial observation).
    if i<=1: return False
    if m.get("message_type")=="observation": return True
    if m.get("role") in ("user","tool"):
        c=m.get("content")
        if isinstance(c,list):
            return any(isinstance(b,dict) and (b.get("type") in ("tool_result","text")) for b in c)
        return isinstance(c,str)
    return False

def analyze_traj(hist):
    """Return list of per-step availability records (as the shim would see them, in order)."""
    recs=[]
    for k in range(len(hist)):
        # simulate the message list up to and including step k, find newest obs
        msgs=hist[:k+1]
        obs=[i for i in range(len(msgs)) if is_obs(i,msgs[i])]
        if not obs: continue
        seg_idx=obs[-1]
        if seg_idx!=k: continue  # only score when newest obs is the latest message (a real decision point)
        seg=txt(msgs[seg_idx].get("content"))
        prior=set()
        for pi in obs[:-1]:
            for l in elig_lines(txt(msgs[pi].get("content"))): prior.add(l)
        se=elig_lines(seg)
        dup=sum(1 for l in se if l in prior)
        frac=dup/max(len(se),1)
        avail=(len(seg)>=MIN_SEG and dup>=MIN_DUP and dup>=1)
        recs.append(dict(seg_chars=len(seg),dup_lines=dup,dup_frac=round(frac,4),available=avail))
    return recs

def main():
    td,out=sys.argv[1],sys.argv[2]
    per_task={}
    for tjf in glob.glob(os.path.join(td,"**","*.traj"),recursive=True):
        tid=os.path.basename(tjf).replace(".traj","")
        try:
            tj=json.load(open(tjf)); hist=tj.get("history") or []
            recs=analyze_traj(hist)
            first_avail=next((r for r in recs if r["available"]), None)
            per_task[tid]=dict(repo=tid.split("__")[0], n_steps=len(recs),
                n_available=sum(1 for r in recs if r["available"]),
                reaches_availability=first_avail is not None,
                first_avail_dupfrac=(first_avail["dup_frac"] if first_avail else None),
                max_dupfrac=max((r["dup_frac"] for r in recs), default=0.0),
                max_seg=max((r["seg_chars"] for r in recs), default=0))
        except Exception as e:
            per_task[tid]=dict(error=str(e))
    tasks=[t for t,v in per_task.items() if "error" not in v]
    reached=[t for t in tasks if per_task[t]["reaches_availability"]]
    avail_fracs=[per_task[t]["first_avail_dupfrac"] for t in reached if per_task[t]["first_avail_dupfrac"] is not None]
    import statistics
    summary=dict(n_tasks=len(tasks), n_reaching_availability=len(reached),
        availability_rate=round(len(reached)/max(len(tasks),1),4),
        total_available_events=sum(per_task[t]["n_available"] for t in tasks),
        repos=dict(collections.Counter(per_task[t]["repo"] for t in reached)),
        first_avail_dupfrac_median=(statistics.median(avail_fracs) if avail_fracs else None),
        n_high=sum(1 for f in avail_fracs if f>0.40), n_mixed=sum(1 for f in avail_fracs if 0<f<=0.40),
        per_task=per_task)
    json.dump(summary, open(out,"w"), indent=1)
    print(json.dumps({k:summary[k] for k in ("n_tasks","n_reaching_availability","availability_rate","total_available_events","repos","first_avail_dupfrac_median","n_high","n_mixed")}, indent=1))

if __name__=="__main__": main()
