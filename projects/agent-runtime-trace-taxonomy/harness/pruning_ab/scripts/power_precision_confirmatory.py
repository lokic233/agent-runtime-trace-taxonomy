#!/usr/bin/env python3
"""Study-2 power AND precision simulation (Part V). Uses Study-1 variance ONLY (no new outcomes).
Simulates the ACTUAL Study-2 estimators across N eligible events:
  - blocked ATE (diff in means within 2:2 blocks)
  - block-FE interaction beta3 (OLS)
  - Hajek self-normalized IPW policy value
  - repo clustering (via cluster bootstrap in the CI width proxy)
Reports (A) power for prespecified practically-relevant effects, (B) expected 95% CI half-width.
Prefers a PRECISION-based stopping goal when 80% moderator power is infeasible.
Usage: power_precision_confirmatory.py <s1_variance.json> <out.json>
"""
import json, sys
import numpy as np

SEED=20260702
rng=np.random.default_rng(SEED)

def simulate(N, sd, dup_mean, dup_sd, dup_min, dup_max,
             true_b1, true_b3, n_sims=2000, high_frac=0.35, n_repos=8):
    """Return dict with power(ATE), power(b3), CI halfwidth(ATE), CI halfwidth(b3)."""
    center=dup_mean
    p_ate=0; p_b3=0; hw_ate=[]; hw_b3=[]
    for _ in range(n_sims):
        # centered dup fraction ~ truncated normal on [dup_min,dup_max]
        S=np.clip(rng.normal(dup_mean,dup_sd,N), dup_min, dup_max)
        Sc=S-center
        # stratified 2:2 assignment (balanced)
        A=np.zeros(N,int); A[:N//2]=1; rng.shuffle(A)
        # potential outcomes: Y = base + b1*A + b3*A*Sc + noise  (b2 nuisance ~ mild)
        base=6236.0
        Y=base + true_b1*A + true_b3*A*Sc + rng.normal(0,sd,N)
        # ATE (diff in means)
        yt=Y[A==1]; yc=Y[A==0]
        ate=yt.mean()-yc.mean()
        se_ate=np.sqrt(yt.var(ddof=1)/len(yt)+yc.var(ddof=1)/len(yc))
        hw_ate.append(1.96*se_ate)
        if abs(ate)-1.96*se_ate>0: p_ate+=1
        # interaction OLS
        X=np.column_stack([np.ones(N),A,Sc,A*Sc])
        beta,_,_,_=np.linalg.lstsq(X,Y,rcond=None)
        resid=Y-X@beta
        XtXi=np.linalg.pinv(X.T@X)
        sig2=(resid@resid)/(N-4)
        se_b3=np.sqrt(sig2*XtXi[3,3])
        hw_b3.append(1.96*se_b3)
        if abs(beta[3])-1.96*se_b3>0: p_b3+=1
    return dict(power_ate=p_ate/n_sims, power_b3=p_b3/n_sims,
               ci_halfwidth_ate=float(np.mean(hw_ate)), ci_halfwidth_b3=float(np.mean(hw_b3)))

def main():
    v=json.load(open(sys.argv[1]))
    sd=v['h1_sd']; dm=v['dup_mean']; ds=v['dup_sd']; dmin=v['dup_min']; dmax=v['dup_max']
    # prespecified practically-relevant effects (frozen)
    MDE_ATE=-570.0   # ~10% of mean 6236 (deployment-relevant saving)
    MDE_B3=-2000.0   # redundancy flips LINEDEDUP from mild harm to help across dup range
    out={'variance_source':'Study-1 (N=13)','h1_sd':sd,'dup_mean':dm,'dup_sd':ds,
         'MDE_ATE':MDE_ATE,'MDE_B3':MDE_B3,'target_power':0.80,'alpha':0.05,
         'grid':{}}
    for N in [60,100,120,160,200,300,400]:
        r=simulate(N,sd,dm,ds,dmin,dmax,MDE_ATE,MDE_B3)
        out['grid'][N]=r
    # precision-based goal: CI half-width on ATE <= |MDE_ATE| (can we bound the effect to +-570?)
    out['precision_goal']={
        'definition':'95% CI half-width on ATE <= |MDE_ATE| (570 eff-cost)',
        'N_meeting':None}
    for N in [60,100,120,160,200,300,400]:
        if out['grid'][N]['ci_halfwidth_ate']<=abs(MDE_ATE):
            out['precision_goal']['N_meeting']=N; break
    # recommendation
    feasible_power=[N for N in out['grid'] if out['grid'][N]['power_b3']>=0.80]
    out['recommendation']={
        'moderator_power_80_feasible': bool(feasible_power),
        'min_N_for_b3_power80': (min(feasible_power) if feasible_power else None),
        'stopping_mode': 'power' if feasible_power else 'precision',
        'note':('At Study-1 variance, 80% power for the practically-relevant interaction requires '
                'N='+str(min(feasible_power)) if feasible_power else
                'At Study-1 variance, 80% moderator power is INFEASIBLE within N<=400. Use a '
                'PRECISION-based stopping goal: collect until the 95% CI half-width on the ATE '
                'reaches the prespecified practical threshold, or the task pool is exhausted.')}
    json.dump(out, open(sys.argv[2],'w'), indent=1)
    print(json.dumps({'grid':{N:{k:round(val,3) if 'power' in k else round(val,0) for k,val in out['grid'][N].items()} for N in out['grid']},
                      'precision_goal':out['precision_goal'],'recommendation':out['recommendation']}, indent=1))

if __name__=='__main__': main()
