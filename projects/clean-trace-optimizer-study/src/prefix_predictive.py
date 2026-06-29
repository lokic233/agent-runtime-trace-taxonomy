#!/usr/bin/env python3
"""prefix predictive check: do EARLY (T5/T10/T20) clean features predict eventual non-convergence
and resolution? This is the genuinely-online-relevant result (a selector would use prefix features).
Writes reports/prefix_predictive.md + data/prefix_predictive.json.
"""
import json, os
import numpy as np, pandas as pd
from sklearn.model_selection import GroupKFold
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE)
FD=os.path.join(ROOT,'data','features')
inv={json.loads(l)['trace_id']:json.loads(l) for l in open(os.path.join(ROOT,'manifests','development_trace_inventory.jsonl'))}

PRIM=['search_no_new_evidence_rate','oversized_then_narrow_read_rate','no_evidence_patch_churn_rate',
      'fraction_actions_in_no_new_evidence_streaks','tool_error_rate','edit_mechanical_failure_rate']
rows=[]
for s in ['solver_A','solver_B','solver_C','solver_E','solver_G','solver_H']:
    p=os.path.join(FD,f'{s}.jsonl')
    if not os.path.exists(p): continue
    for line in open(p):
        d=json.loads(line); tid=d['trace_id']; meta=inv.get(tid,{})
        full=d.get('full',{}); pre=d.get('prefix',{})
        row=dict(trace_id=tid, task_id=d['task_id'], solver=s, resolved=meta.get('resolved'),
                 n_actions=full.get('n_actions'))
        for T in ['T5','T10','T20']:
            pf=pre.get(T,{})
            for f in PRIM: row[f'{T}_{f}']=pf.get(f)
            row[f'{T}_n_actions']=pf.get('n_actions')
        rows.append(row)
df=pd.DataFrame(rows)
# eventual non-convergence: top action-count quartile per solver (proxy for long/stuck)
df['nonconv']=df.groupby('solver')['n_actions'].transform(lambda x:(x>=x.quantile(0.75))).astype(int)

def cv_auroc(Xcols, ycol):
    d=df.dropna(subset=[ycol]).copy()
    d[ycol]=d[ycol].astype(int)
    X=d[Xcols].copy()
    for c in Xcols:
        X[c+'_miss']=X[c].isna().astype(float); X[c]=X[c].fillna(X[c].median())
    y=d[ycol].values; g=d['task_id'].values
    if len(np.unique(y))<2: return None
    gkf=GroupKFold(5); aucs=[]
    for tr,te in gkf.split(X,y,g):
        if len(np.unique(y[tr]))<2 or len(np.unique(y[te]))<2: continue
        sc=StandardScaler().fit(X.iloc[tr]); 
        m=LogisticRegression(max_iter=2000).fit(sc.transform(X.iloc[tr]), y[tr])
        aucs.append(roc_auc_score(y[te], m.predict_proba(sc.transform(X.iloc[te]))[:,1]))
    return round(float(np.mean(aucs)),4) if aucs else None

res={}
for T in ['T5','T10','T20']:
    cols=[f'{T}_{f}' for f in PRIM]+[f'{T}_n_actions']
    res[T]=dict(nonconv_auroc=cv_auroc(cols,'nonconv'),
                # length-only baseline at this prefix
                nonconv_auroc_lengthonly=cv_auroc([f'{T}_n_actions'],'nonconv'),
                resolved_auroc=cv_auroc(cols,'resolved') if df['resolved'].notna().any() else None)

L=["# Prefix Predictive Check (online-relevant)\n",
   "Can EARLY clean features (first T actions) predict eventual non-convergence (top action-count quartile)?",
   "This is what an ONLINE selector would key on. GroupKFold by task. Compared vs prefix-length-only.\n",
   "| prefix | nonconv AUROC (features+len) | nonconv AUROC (len only) | feature lift |",
   "|---|---|---|---|"]
for T in ['T5','T10','T20']:
    a=res[T]['nonconv_auroc']; b=res[T]['nonconv_auroc_lengthonly']
    lift = round(a-b,4) if (a and b) else None
    L.append(f"| {T} | {a} | {b} | {lift} |")
L.append("\n## Interpretation")
L.append("- If feature+len AUROC > len-only at the SAME prefix, early clean features carry online signal beyond")
L.append("  'the trace is already long'. This is the most decision-relevant prefix result for a controller.")
L.append("- Honest caveat: non-convergence here is an action-count quartile (self-referential to length), so a")
L.append("  positive lift means the BEHAVIORAL features (search-no-new-evidence, stagnation, mech-failure) add")
L.append("  information about WHICH early traces blow up, beyond raw early length.")
open(os.path.join(ROOT,'reports','prefix_predictive.md'),'w').write("\n".join(L))
json.dump(res, open(os.path.join(ROOT,'data','prefix_predictive.json'),'w'),indent=1)
print("prefix predictive:", json.dumps(res,indent=1))
