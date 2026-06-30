#!/usr/bin/env python3
"""Isolate intelligence tax from dose: per-task drift vs (chars_removed, removal_type)."""
import json, os, glob, statistics as st
BASE="/data/users/dengcchi/prune_ab"
G=set(json.load(open("/tmp/golden50.json")))

def per_task_calls(arm):
    d={}
    for f in glob.glob(f"{BASE}/arms/{arm}/*/*.traj"):
        tid=os.path.basename(f).replace(".traj","")
        if tid not in G: continue
        try: d[tid]=json.load(open(f))["info"]["model_stats"].get("api_calls",0)
        except: pass
    return d

def per_task_dose(ledger):
    """per-task total chars removed."""
    d={}
    if not os.path.exists(ledger): return d
    for l in open(ledger):
        try:
            x=json.loads(l); t=x.get("task_id")
            if not t or str(t).startswith(("UNKNOWN","NO_")): continue
            d[t]=d.get(t,0)+x.get("characters_removed",0)
        except: pass
    return d

c0=per_task_calls("stable_C0_identity")
# build per-task records: (drift=call_ratio, dose=chars_removed_per_task, type)
TYPE_REDUNDANT={"LINEDEDUP_e4":"logs/e4/ledger_LINEDEDUP_e4.jsonl","RETRIEVREF_e4":"logs/e4/ledger_RETRIEVREF_e4.jsonl"}
TYPE_DESTRUCTIVE={"CAP1K_stable":"logs/stable/ledger_CAP1K_stable.jsonl","CAP500_stable":"logs/stable/ledger_CAP500_stable.jsonl","SIGNAL_e4":"logs/e4/ledger_SIGNAL_e4.jsonl"}
ARM={"LINEDEDUP_e4":"e4_LINEDEDUP_e4","RETRIEVREF_e4":"e4_RETRIEVREF_e4","CAP1K_stable":"stable_CAP1K_stable","CAP500_stable":"stable_CAP500_stable","SIGNAL_e4":"e4_SIGNAL_e4"}

recs=[]  # (dose_kchars, is_destructive, drift)
for grp,is_destr in [(TYPE_REDUNDANT,0),(TYPE_DESTRUCTIVE,1)]:
    for m,led in grp.items():
        calls=per_task_calls(ARM[m]); dose=per_task_dose(f"{BASE}/{led}")
        for t in set(calls)&set(c0)&set(dose):
            if c0[t]>0 and dose[t]>0:
                recs.append((dose[t]/1000.0, is_destr, calls[t]/c0[t]))
print(f"n records: {len(recs)}")
# bin by dose, compare drift within dose bins across types (stratified — controls dose)
import statistics as st
bins=[(0,5),(5,15),(15,40),(40,999)]
print(f"\n{'dose bin (kchars)':18s}{'redundant drift':>17s}{'destructive drift':>19s}{'n_r/n_d':>10s}")
for lo,hi in bins:
    rr=[d for k,t,d in recs if lo<=k<hi and t==0]
    dd=[d for k,t,d in recs if lo<=k<hi and t==1]
    rstr=f"{st.median(rr):.2f}" if rr else "-"
    dstr=f"{st.median(dd):.2f}" if dd else "-"
    print(f"  {lo}-{hi:>3} kchars     {rstr:>15s}{dstr:>19s}{f'{len(rr)}/{len(dd)}':>10s}")
print("\n  => If destructive drift > redundant drift AT THE SAME DOSE BIN, the intelligence tax")
print("     is real and SEPARABLE from dose. (redundant=exact-dup/retrievable; destructive=truncation/skim)")
# simple OLS: drift ~ dose + is_destructive
import statistics
n=len(recs)
xs_dose=[r[0] for r in recs]; xs_type=[r[1] for r in recs]; ys=[r[2] for r in recs]
# manual 2-var OLS
def ols2(x1,x2,y):
    n=len(y); mx1=st.mean(x1);mx2=st.mean(x2);my=st.mean(y)
    # normal equations (2 predictors + intercept) via simple solve
    import itertools
    s11=sum((a-mx1)**2 for a in x1); s22=sum((a-mx2)**2 for a in x2)
    s12=sum((x1[i]-mx1)*(x2[i]-mx2) for i in range(n))
    s1y=sum((x1[i]-mx1)*(y[i]-my) for i in range(n)); s2y=sum((x2[i]-mx2)*(y[i]-my) for i in range(n))
    det=s11*s22-s12*s12
    if abs(det)<1e-9: return None
    b1=(s22*s1y-s12*s2y)/det; b2=(s11*s2y-s12*s1y)/det
    return b1,b2
res=ols2(xs_dose,xs_type,ys)
if res:
    print(f"\n  OLS drift ~ dose(kchars) + is_destructive:")
    print(f"    dose coef = {res[0]:+.4f} per kchar  (drift added per 1k chars removed, any type)")
    print(f"    is_destructive coef = {res[1]:+.3f}  (EXTRA drift from destructive removal, dose-adjusted)")
    print(f"    => is_destructive coef >0 and meaningful => INTELLIGENCE TAX is real beyond dose")
m=json.load(open(f"{BASE}/results/pruning_ab/mechanism_effects.json"))
m["intelligence_tax_dose_controlled"]={"ols_dose_coef":round(res[0],4) if res else None,"ols_destructive_coef":round(res[1],3) if res else None,"n":len(recs)}
json.dump(m,open(f"{BASE}/results/pruning_ab/mechanism_effects.json","w"),indent=1,default=str)
