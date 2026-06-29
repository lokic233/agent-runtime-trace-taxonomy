#!/usr/bin/env python3
import json, os
import pandas as pd, numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE)
df=pd.read_parquet(os.path.join(ROOT,'data','baseline_trace_feature_table.parquet'))
d=json.load(open(os.path.join(ROOT,'data','correlation_results.json')))
FD=os.path.join(ROOT,'figures')

PRIMARY=['search_no_new_evidence_rate','oversized_then_narrow_read_rate','no_evidence_patch_churn_rate',
         'fraction_actions_in_no_new_evidence_streaks','tool_error_rate','redundant_reread_rate']
# 1) feature distributions by solver (violin-ish via boxplot)
fig,axes=plt.subplots(2,3,figsize=(16,9))
order=['solver_A','solver_B','solver_C','solver_E','solver_F','solver_G','solver_H']
for ax,f in zip(axes.flat, PRIMARY):
    data=[df[df.solver_alias==s][f].dropna().values for s in order]
    ax.boxplot(data, tick_labels=[s.replace('solver_','') for s in order], showfliers=False)
    ax.set_title(f, fontsize=10); ax.tick_params(axis='x', labelsize=8)
plt.suptitle('Clean feature distributions by solver (boxplot, no fliers)')
plt.tight_layout(); plt.savefig(os.path.join(FD,'feature_distributions','by_solver.png'),dpi=90); plt.close()

# 2) RQ2 resolution forest plot (beta + CI)
rq2=d['results']['RQ2_resolution']
feats=list(rq2.keys()); betas=[float(rq2[f]['beta']) for f in feats]
los=[float(rq2[f]['lo']) if rq2[f].get('lo') is not None else b for f,b in zip(feats,betas)]
his=[float(rq2[f]['hi']) if rq2[f].get('hi') is not None else b for f,b in zip(feats,betas)]
fig,ax=plt.subplots(figsize=(9,6))
y=np.arange(len(feats))
ax.errorbar(betas,y,xerr=[np.array(betas)-np.array(los),np.array(his)-np.array(betas)],fmt='o',capsize=4)
ax.axvline(0,color='gray',ls='--'); ax.set_yticks(y); ax.set_yticklabels(feats,fontsize=9)
ax.set_xlabel('standardized logistic beta (resolution), task-clustered 95% CI')
ax.set_title('RQ2: feature -> resolution (CORE A/B/C)')
plt.tight_layout(); plt.savefig(os.path.join(FD,'correlation','rq2_resolution_forest.png'),dpi=90); plt.close()

# 3) ablation bars (the headline)
ab=d['ablation']
fig,axes=plt.subplots(1,2,figsize=(13,5))
ks=['A_nevents','B_meta','C_meta_feats']
axes[0].bar(ks,[ab['cost'][k]['cv_r2'] for k in ks],color=['#bbb','#88a','#5a5']); axes[0].set_ylim(0.99,1.0)
axes[0].set_title('Cost CV R^2 (n_actions)'); axes[0].set_ylabel('R^2')
axes[1].bar(ks,[ab['resolution'][k]['auroc'] for k in ks],color=['#bbb','#88a','#5a5']); axes[1].set_ylim(0.5,1.0)
axes[1].set_title('Resolution CV AUROC (A/B/C)'); axes[1].set_ylabel('AUROC')
for ax in axes:
    for i,k in enumerate(ks):
        v=(ab['cost'][k]['cv_r2'] if ax is axes[0] else ab['resolution'][k]['auroc'])
        ax.text(i,v,f"{v:.4f}" if ax is axes[0] else f"{v:.3f}",ha='center',va='bottom',fontsize=9)
plt.suptitle('Predictive ablation: A(length) -> B(+meta) -> C(+clean features). Clean features add ~0 OOS.')
plt.tight_layout(); plt.savefig(os.path.join(FD,'correlation','ablation_ABC.png'),dpi=90); plt.close()
print("figures written:", os.listdir(os.path.join(FD,'correlation')), os.listdir(os.path.join(FD,'feature_distributions')))
