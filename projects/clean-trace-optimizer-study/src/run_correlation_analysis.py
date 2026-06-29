#!/usr/bin/env python3
"""run_correlation_analysis.py — Phase C clean correlation study.
RQ1 cost(n_actions), RQ2 resolution, RQ3 non-convergence + sensitivity + predictive ablation A/B/C.
Uses statsmodels if present; else sklearn/scipy fallback. Task-clustered bootstrap CIs. BH correction.
"""
import json, os, warnings, itertools
import numpy as np, pandas as pd
from scipy import stats
warnings.filterwarnings('ignore')
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE)
np.random.seed(20260628)

try:
    import statsmodels.formula.api as smf
    import statsmodels.api as sm
    HAVE_SM=True
except Exception:
    HAVE_SM=False
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GroupKFold
from sklearn.metrics import roc_auc_score, average_precision_score, log_loss, brier_score_loss, mean_absolute_error, r2_score

df=pd.read_parquet(os.path.join(ROOT,'data','baseline_trace_feature_table.parquet'))
PRIMARY=['search_no_new_evidence_rate','oversized_then_narrow_read_rate','no_evidence_patch_churn_rate',
         'edit_mechanical_failure_rate','post_edit_test_gap','fraction_actions_in_no_new_evidence_streaks',
         'tool_error_rate','environment_setup_rate','redundant_reread_rate']
CORE=['solver_A','solver_B','solver_C']   # core development cohort for RQ2

def z(s):
    s=pd.to_numeric(s, errors='coerce'); return (s-s.mean())/s.std(ddof=0)

# ---------- RQ helpers ----------
def std_beta_ci(y, x, controls_df, clusters, logistic=False, nboot=600):
    """standardized beta of x on y controlling for one-hot(controls); task-clustered bootstrap CI."""
    d=pd.concat([y.rename('y'), x.rename('x'), controls_df.reset_index(drop=True), clusters.rename('cl').reset_index(drop=True)],axis=1).dropna()
    if len(d)<40 or d['x'].nunique()<3: return None
    Xc=pd.get_dummies(d[controls_df.columns], drop_first=True, dtype=float)
    Xc=Xc.loc[:, Xc.std()>0]
    Xfull=pd.concat([d[['x']].reset_index(drop=True), Xc.reset_index(drop=True)],axis=1).astype(float)
    yv=d['y'].astype(float).values
    def fit(Xv,yv):
        if logistic:
            if len(np.unique(yv))<2: return np.nan
            m=LogisticRegression(max_iter=2000, C=1e6, solver='lbfgs'); m.fit(Xv,yv); return m.coef_[0][0]
        else:
            m=LinearRegression(); m.fit(Xv,yv); return m.coef_[0]
    beta=fit(Xfull.values, yv)
    # bootstrap over clusters (tasks)
    cls=d['cl'].values; uniq=np.unique(cls); boots=[]
    idx_by={c:np.where(cls==c)[0] for c in uniq}
    for _ in range(nboot):
        pick=np.random.choice(uniq, len(uniq), replace=True)
        rows=np.concatenate([idx_by[c] for c in pick])
        try:
            b=fit(Xfull.values[rows], yv[rows])
            if not np.isnan(b): boots.append(b)
        except Exception: pass
    if len(boots)<50: return dict(beta=float(beta), lo=None, hi=None, n=int(len(d)))
    lo,hi=np.percentile(boots,[2.5,97.5])
    return dict(beta=float(beta), lo=float(lo), hi=float(hi), n=int(len(d)), nboot=len(boots))

def bh(pvals):
    p=np.array(pvals,dtype=float); m=len(p); order=np.argsort(p); adj=np.empty(m)
    prev=1.0
    for i in range(m-1,-1,-1):
        rank=i+1; val=p[order[i]]*m/rank; prev=min(prev,val); adj[order[i]]=min(prev,1.0)
    return adj

results={'RQ1_cost':{}, 'RQ2_resolution':{}, 'RQ3_nonconv':{}}

# ===== RQ1 cost (log1p n_actions) =====
df['log_actions']=np.log1p(df['n_actions'])
df['log_events']=np.log1p(df['n_events'])
controls=df[['solver_alias','source_harness','repo']]
pv=[]; keys=[]
for f in PRIMARY:
    r=std_beta_ci(df['log_actions'], z(df[f]), controls, df['task_id'])
    if r:
        sp=stats.spearmanr(df[f], df['n_actions'], nan_policy='omit')
        r['spearman']=round(float(sp.statistic),3); r['spearman_p']=float(sp.pvalue)
        results['RQ1_cost'][f]=r; pv.append(sp.pvalue); keys.append(f)
adj=bh(pv)
for k,a in zip(keys,adj): results['RQ1_cost'][k]['bh_p']=float(a)

# ===== RQ2 resolution (CORE cohort A/B/C) =====
core=df[df['solver_alias'].isin(CORE)].copy()
core=core[core['resolved'].notna()]
core['resolved_int']=core['resolved'].astype(int)
ctrl2=core[['solver_alias','source_harness','repo']]
pv=[]; keys=[]
for f in PRIMARY:
    r=std_beta_ci(core['resolved_int'], z(core[f]), ctrl2, core['task_id'], logistic=True)
    if r:
        sp=stats.spearmanr(core[f], core['resolved_int'], nan_policy='omit')
        r['spearman']=round(float(sp.statistic),3); r['spearman_p']=float(sp.pvalue)
        results['RQ2_resolution'][f]=r; pv.append(sp.pvalue); keys.append(f)
adj=bh(pv)
for k,a in zip(keys,adj): results['RQ2_resolution'][k]['bh_p']=float(a)

# ===== RQ3 non-convergence (proxy: no SUBMIT-ish tail => use n_actions>=95th pct per solver as 'capped') =====
caps=df.groupby('solver_alias')['n_actions'].transform(lambda s: s>=s.quantile(0.95))
df['nonconv']=caps.astype(int)
ctrl3=df[['solver_alias','source_harness','repo']]
for f in PRIMARY:
    r=std_beta_ci(df['nonconv'], z(df[f]), ctrl3, df['task_id'], logistic=True)
    if r:
        results['RQ3_nonconv'][f]=r

# ===== Predictive ablation A/B/C (GroupKFold by task) =====
def onehot(frame, cols):
    X=pd.get_dummies(frame[cols], drop_first=True, dtype=float)
    return X

abl={'cost':{}, 'resolution':{}}
# COST on full df
d=df.dropna(subset=['log_actions','n_events']).copy()
feat_cols=[f for f in PRIMARY]
# impute primary features with median FLAG (don't fill 0): add missing indicator + median for model only
Xfeat=d[feat_cols].copy()
for c in feat_cols:
    Xfeat[c+'_miss']=Xfeat[c].isna().astype(float)
    Xfeat[c]=Xfeat[c].fillna(Xfeat[c].median())
groups=d['task_id']; gkf=GroupKFold(n_splits=5)
def cv_cost(Xbuild):
    maes=[]; r2s=[]
    for tr,te in gkf.split(Xbuild, d['log_actions'], groups):
        m=LinearRegression().fit(Xbuild.iloc[tr], d['log_actions'].iloc[tr])
        p=m.predict(Xbuild.iloc[te]); maes.append(mean_absolute_error(d['log_actions'].iloc[te],p)); r2s.append(r2_score(d['log_actions'].iloc[te],p))
    return float(np.mean(r2s)), float(np.mean(maes))
A=d[['log_events']].astype(float)
B=pd.concat([d[['log_events']].astype(float).reset_index(drop=True), onehot(d,['solver_alias','source_harness','repo']).reset_index(drop=True)],axis=1)
C=pd.concat([B.reset_index(drop=True), Xfeat.reset_index(drop=True)],axis=1)
for name,X in [('A_nevents',A),('B_meta',B),('C_meta_feats',C)]:
    r2,mae=cv_cost(X.astype(float)); abl['cost'][name]=dict(cv_r2=round(r2,4), mae=round(mae,4))

# RESOLUTION on CORE
dc=core.dropna(subset=['log_events']).copy()
Xf=dc[feat_cols].copy()
for c in feat_cols:
    Xf[c+'_miss']=Xf[c].isna().astype(float); Xf[c]=Xf[c].fillna(Xf[c].median())
g2=dc['task_id']; y2=dc['resolved_int'].values
def cv_res(Xbuild):
    aucs=[]; aps=[]; lls=[]; brs=[]
    for tr,te in gkf.split(Xbuild,y2,g2):
        if len(np.unique(y2[tr]))<2: continue
        m=LogisticRegression(max_iter=3000,C=1.0).fit(StandardScaler().fit_transform(Xbuild.iloc[tr]), y2[tr])
        Xte=StandardScaler().fit(Xbuild.iloc[tr]).transform(Xbuild.iloc[te])
        p=m.predict_proba(Xte)[:,1]
        if len(np.unique(y2[te]))>1:
            aucs.append(roc_auc_score(y2[te],p)); aps.append(average_precision_score(y2[te],p))
            lls.append(log_loss(y2[te],p,labels=[0,1])); brs.append(brier_score_loss(y2[te],p))
    return (float(np.mean(aucs)) if aucs else None, float(np.mean(aps)) if aps else None,
            float(np.mean(lls)) if lls else None, float(np.mean(brs)) if brs else None)
A2=dc[['log_events']].astype(float)
B2=pd.concat([dc[['log_events']].astype(float).reset_index(drop=True), onehot(dc,['solver_alias','source_harness','repo']).reset_index(drop=True)],axis=1)
C2=pd.concat([B2.reset_index(drop=True), Xf.reset_index(drop=True)],axis=1)
for name,X in [('A_nevents',A2),('B_meta',B2),('C_meta_feats',C2)]:
    auc,ap,ll,br=cv_res(X.astype(float)); abl['resolution'][name]=dict(auroc=round(auc,4) if auc else None, auprc=round(ap,4) if ap else None, logloss=round(ll,4) if ll else None, brier=round(br,4) if br else None)

# ===== negative controls =====
neg={}
# permutation: shuffle a strong feature across tasks -> beta should vanish
import copy
permuted=df.copy(); permuted['perm_feat']=np.random.permutation(df['tool_error_rate'].values)
r=std_beta_ci(df['log_actions'], z(permuted['perm_feat']), controls, df['task_id'])
neg['permutation_tool_error_on_cost']=r
# random synthetic
df['rand']=np.random.randn(len(df))
neg['random_feature_on_cost']=std_beta_ci(df['log_actions'], z(df['rand']), controls, df['task_id'])
core=core.copy(); core['rand2']=np.random.randn(len(core))
neg['random_feature_on_resolution']=std_beta_ci(core['resolved_int'], z(core['rand2']), ctrl2, core['task_id'], logistic=True)

out=dict(results=results, ablation=abl, negative_controls=neg,
         meta=dict(have_statsmodels=HAVE_SM, n_total=len(df), n_core=len(core), core=CORE, primary=PRIMARY))
json.dump(out, open(os.path.join(ROOT,'data','correlation_results.json'),'w'), indent=1, default=str)
print("=== ABLATION cost ==="); print(abl['cost'])
print("=== ABLATION resolution ==="); print(abl['resolution'])
print("=== RQ2 (resolution) betas ===")
for f,r in results['RQ2_resolution'].items():
    print(f"  {f}: beta={r['beta']:.3f} CI=({r.get('lo')},{r.get('hi')}) bh_p={r.get('bh_p'):.3g} n={r['n']}")
print("=== negative controls ==="); print({k:(v['beta'] if v else None) for k,v in neg.items()})
