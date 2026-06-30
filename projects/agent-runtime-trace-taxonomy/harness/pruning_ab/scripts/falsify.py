#!/usr/bin/env python3
import json, os, statistics as st, random
BASE="/data/users/dengcchi/prune_ab"
INT10=set(json.load(open("/tmp/interesting10.json")))
feats={r["task_id"]:r for r in (json.loads(l) for l in open(f"{BASE}/results/pruning_ab/pre_treatment_features.jsonl"))}

def eff_aa(method,rep,tasks):
    f=f"{BASE}/logs/phase34/ledger_{method}_rep{rep}.jsonl"; a={}
    if not os.path.exists(f): return a
    for l in open(f):
        try:
            d=json.loads(l);t=d.get("task_id")
            if not t or t not in tasks: continue
            ir=(d.get("input_tokens")or 0);cr=(d.get("cache_read_tokens")or 0);cc=(d.get("cache_creation_tokens")or 0);op=(d.get("output_tokens")or 0)
            a[t]=a.get(t,0)+ir+cr*.1+cc*1.25+op*5
        except:pass
    return a

print("="*70)
print("FALSIFICATION: SHAM COST negative control (A/A 10 tasks, 5 reps)")
print("Does dup_line_ratio predict SHAM's cost 'effect'? It SHOULDN'T (SHAM = no-op).")
print("="*70)
# avg SHAM and C0 cost per task across reps, then delta
def avg_cost(method):
    per={}
    for t in INT10:
        vals=[]
        for r in range(1,6):
            a=eff_aa(method,r,{t})
            if t in a: vals.append(a[t])
        if vals: per[t]=st.mean(vals)
    return per
c0a=avg_cost("C0_identity"); shama=avg_cost("SHAM")
common=sorted(set(c0a)&set(shama))
sham_delta={t:100*(c0a[t]-shama[t])/c0a[t] for t in common if c0a[t]>0}
# spearman with dup_ratio
def _rank(v):
    idx=sorted(range(len(v)),key=lambda i:v[i]);r=[0]*len(v)
    for k,i in enumerate(idx):r[i]=k
    return r
def sp(deltas,fk):
    ts=[t for t in deltas if t in feats]; 
    if len(ts)<4: return None
    xs=[feats[t][fk] for t in ts];ys=[deltas[t] for t in ts];rx=_rank(xs);ry=_rank(ys);n=len(xs)
    return 1-6*sum((rx[i]-ry[i])**2 for i in range(n))/(n*(n*n-1))
print(f"\nSHAM mean cost-delta vs C0: {st.mean(list(sham_delta.values())):+.1f}% (should be ~0 if no-op)")
print(f"spearman(SHAM cost-delta, dup_line_ratio) = {sp(sham_delta,'dup_line_ratio')}")
print(f"  => if |spearman| is large, dup_ratio predicts NOISE/instability, not treatment benefit")

print("\n"+"="*70)
print("FALSIFICATION: REPO-CLUSTER BOOTSTRAP on LINEDEDUP overall saving")
print("="*70)
def ledger(led):
    a={}
    for l in open(f"{BASE}/{led}"):
        try:
            d=json.loads(l);t=d.get("task_id")
            if not t or str(t).startswith(("UNKNOWN","NO_")):continue
            ir=(d.get("input_tokens")or 0);cr=(d.get("cache_read_tokens")or 0);cc=(d.get("cache_creation_tokens")or 0);op=(d.get("output_tokens")or 0)
            a[t]=a.get(t,0)+ir+cr*.1+cc*1.25+op*5
        except:pass
    return a
c0=ledger("logs/stable/ledger_C0_identity.jsonl");ld=ledger("logs/e4/ledger_LINEDEDUP_e4.jsonl")
common=sorted(set(c0)&set(ld)&set(feats))
from collections import defaultdict
byrepo=defaultdict(list)
for t in common: byrepo[feats[t]["repo"]].append(t)
repos=list(byrepo)
random.seed(2); boots=[]
for _ in range(2000):
    samp=[random.choice(repos) for _ in repos]  # resample REPOS (cluster)
    ts=[t for rp in samp for t in byrepo[rp]]
    ct=sum(c0[t] for t in ts);lt=sum(ld[t] for t in ts)
    if ct>0: boots.append(100*(ct-lt)/ct)
boots.sort()
print(f"\nLINEDEDUP overall saving: point=+6.3%, repo-cluster 95% CI = [{boots[50]:+.1f}%, {boots[1949]:+.1f}%]")
print(f"  => if CI includes 0 (or negative), the saving is NOT robust to repo clustering")
json.dump({"sham_cost_delta_mean":round(st.mean(list(sham_delta.values())),1),"sham_dup_spearman":sp(sham_delta,'dup_line_ratio'),
           "linededup_repo_cluster_ci":[round(boots[50],1),round(boots[1949],1)]},
          open(f"{BASE}/results/pruning_ab/falsification.json","w"),indent=1,default=str)
print("\nfalsification.json written")
