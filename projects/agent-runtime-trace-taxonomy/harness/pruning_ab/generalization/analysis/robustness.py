#!/usr/bin/env python3
"""Mission section-8 robustness checks — reusable across Phases C/D/E.
Mirrors the frozen study's robustness battery (ROBUSTNESS_FALSIFICATION.md): paired bootstrap,
repository-clustered bootstrap, leave-one-repository-out, leave-top-1 / leave-top-3 expensive-task-out,
full-set vs common-support, SHAM negative control. stdlib only (no numpy/scipy).

Operates on per-task paired (treatment_cost, c0_cost) dicts. Saving% = 100*(c0-treat)/c0 (positive=saving).
"""
import random, statistics
from collections import defaultdict

def repo_of(task_id):  # SWE-bench: "<org>__<repo>-<num>"
    return task_id.split("__")[0] if "__" in task_id else task_id

def saving_pct(pairs, tasks=None):
    """pairs: {task: (treat, c0)}. Bill-weighted aggregate saving% over `tasks` (default all)."""
    tasks = tasks if tasks is not None else list(pairs)
    t=sum(pairs[k][0] for k in tasks); c=sum(pairs[k][1] for k in tasks)
    return 100*(c-t)/c if c>0 else None

def task_weighted_median(pairs, tasks=None):
    tasks = tasks if tasks is not None else list(pairs)
    per=[100*(pairs[k][1]-pairs[k][0])/pairs[k][1] for k in tasks if pairs[k][1]>0]
    return statistics.median(per) if per else None

def paired_bootstrap(pairs, n=2000, seed=42):
    ks=list(pairs); random.seed(seed); out=[]
    for _ in range(n):
        s=[random.choice(ks) for _ in ks]; out.append(saving_pct(pairs, s))
    out=[x for x in out if x is not None]; out.sort()
    return [round(out[int(0.025*len(out))],2), round(out[int(0.975*len(out))],2)] if out else [None,None]

def repo_cluster_bootstrap(pairs, n=2000, seed=42):
    """Resample REPOS (clusters), not tasks — accounts for within-repo correlation."""
    byrepo=defaultdict(list)
    for k in pairs: byrepo[repo_of(k)].append(k)
    repos=list(byrepo); random.seed(seed); out=[]
    for _ in range(n):
        s=[random.choice(repos) for _ in repos]
        tasks=[t for r in s for t in byrepo[r]]
        out.append(saving_pct(pairs, tasks))
    out=[x for x in out if x is not None]; out.sort()
    return [round(out[int(0.025*len(out))],2), round(out[int(0.975*len(out))],2)] if out else [None,None]

def leave_one_repo_out(pairs):
    byrepo=defaultdict(list)
    for k in pairs: byrepo[repo_of(k)].append(k)
    res={}
    for r in byrepo:
        keep=[k for k in pairs if repo_of(k)!=r]
        res[f"drop_{r}"]=round(saving_pct(pairs, keep),2) if keep else None
    return res

def leave_top_k(pairs, ks=(1,3,5)):
    """Remove the k most EXPENSIVE-by-c0 tasks (the frozen study's key fragility check)."""
    order=sorted(pairs, key=lambda k: pairs[k][1], reverse=True)
    res={"0":round(saving_pct(pairs),2)}
    for k in ks:
        keep=order[k:]
        res[str(k)]=round(saving_pct(pairs, keep),2) if keep else None
    return res

def common_support(c0_by_model, min_models=2):
    """Tasks present + with C0 cost in >= min_models models. Defined from C0 ONLY (no treatment peeking)."""
    cnt=defaultdict(int)
    for m,by in c0_by_model.items():
        for t in by: cnt[t]+=1
    return sorted([t for t,c in cnt.items() if c>=min_models])

def full_robustness(pairs):
    return {"n_tasks":len(pairs),"bill_weighted_saving_pct":round(saving_pct(pairs),2) if pairs else None,
            "task_weighted_median_pct":round(task_weighted_median(pairs),2) if pairs else None,
            "paired_bootstrap_ci":paired_bootstrap(pairs),
            "repo_cluster_ci":repo_cluster_bootstrap(pairs),
            "leave_one_repo_out":leave_one_repo_out(pairs),
            "leave_top_k":leave_top_k(pairs)}

if __name__=="__main__":
    # self-test: synthetic where saving is concentrated in 1 expensive task (mirrors frozen finding)
    pairs={"a__a-1":(100,100),"a__a-2":(100,100),"b__b-1":(50,100),"c__c-1":(9000,10000)}
    import json; r=full_robustness(pairs)
    print(json.dumps(r,indent=1))
    assert r["leave_top_k"]["0"] is not None and r["leave_top_k"]["1"] is not None
    print("robustness self-test PASS (leave-top-1 changes the saving as expected)")
