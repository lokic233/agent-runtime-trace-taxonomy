#!/usr/bin/env python3
"""Study-1 statistical reconciliation — CORRECTED estimators.
Reads ONLY immutable Study-1 raw artifacts. Never rewrites them.
numpy-only. Produces:
  - policy_value_corrected.json  (Hajek self-normalized IPW + cross-fitted DR + repo-bootstrap CI)
  - placebo_distribution.json    (>=5000 deterministic placebo moderators + block-randomization test)
  - study1_reconciliation.json   (verdict corrections + risk-diff Wilson/Newcombe CI)
Usage: study1_reconcile.py <formal_dir> <out_dir>
"""
import json, os, sys, hashlib, collections
import numpy as np

SEED=20260701
DUP_THRESHOLD=0.40
N_PLACEBO=5000

def load_jsonl(p): return [json.loads(l) for l in open(p) if l.strip()]
def sha256_full(p): return hashlib.sha256(open(p,'rb').read()).hexdigest()

def join_h3(events):
    by=collections.defaultdict(list)
    for e in events:
        if e.get("task_id"): by[e["task_id"]].append(e)
    rows=[]
    for tid,evs in by.items():
        evs.sort(key=lambda e:e.get("call_index",0))
        exp=[e for e in evs if e.get("experimental_event")]
        if not exp: continue
        iv=exp[0]
        after=[e for e in evs if e.get("call_index",0)>=iv.get("call_index",0)]
        costs=[e.get("effective_cost_h1") for e in after[:3] if e.get("effective_cost_h1") is not None]
        rows.append(dict(task_id=tid, repo=iv.get("repo",""),
            A=1 if iv.get("assignment")=="LINEDEDUP" else 0,
            assignment=iv.get("assignment"), stratum=iv.get("moderator_stratum"),
            dup_frac=iv.get("duplicate_line_fraction",0.0), seg_chars=iv.get("segment_chars",0),
            calls_so_far=iv.get("call_index",0), block_id=iv.get("block_id"),
            h1=iv.get("effective_cost_h1"), h3=sum(costs) if costs else None,
            infra=any(e.get("infrastructure_failure") for e in after[:3])))
    return rows

# ---------- policy value estimators ----------
def hajek_ipw(rows, pi, p=0.5):
    """Self-normalized IPW: sum(w_i Y_i)/sum(w_i), w_i = 1{A_i==pi_i}/p."""
    num=0.0; den=0.0
    for x in rows:
        w = (1.0/p) if x['A']==pi(x) else 0.0
        num += w*x['h1']; den += w
    return num/den if den>0 else float('nan')

def dr_crossfit(rows, pi, p=0.5, seed=SEED):
    """Cross-fitted DR: leave-one-repo-out outcome model (stratum x arm mean on training folds)."""
    repos=sorted(set(x['repo'] for x in rows))
    ests=[]
    for x in rows:
        train=[r for r in rows if r['repo']!=x['repo']]
        # outcome model from training fold
        om={}
        for st in set(r['stratum'] for r in train):
            for aa in (0,1):
                v=[r['h1'] for r in train if r['stratum']==st and r['A']==aa]
                om[(st,aa)]=np.mean(v) if v else None
        a_star=pi(x)
        mhat=om.get((x['stratum'],a_star))
        if mhat is None:
            v=[r['h1'] for r in train if r['A']==a_star]
            mhat=np.mean(v) if v else x['h1']
        mhat_obs=om.get((x['stratum'],x['A']))
        if mhat_obs is None:
            v=[r['h1'] for r in train if r['A']==x['A']]
            mhat_obs=np.mean(v) if v else x['h1']
        ind=1.0 if x['A']==a_star else 0.0
        ests.append(mhat + ind/p*(x['h1']-mhat_obs))
    return float(np.mean(ests))

def repo_bootstrap_policy_diff(rows, pi_a, pi_b, estimator, B=5000, seed=SEED):
    """Repo-clustered bootstrap CI for V(pi_a)-V(pi_b)."""
    rng=np.random.default_rng(seed)
    repos=sorted(set(x['repo'] for x in rows))
    byrepo={r:[x for x in rows if x['repo']==r] for r in repos}
    diffs=[]
    for _ in range(B):
        pick=rng.choice(repos,len(repos),replace=True)
        samp=[]
        for r in pick: samp+=byrepo[r]
        if len(samp)<2: continue
        try:
            da=estimator(samp,pi_a); db=estimator(samp,pi_b)
            if np.isfinite(da) and np.isfinite(db): diffs.append(da-db)
        except Exception: pass
    if not diffs: return (None,None,None)
    d=np.array(diffs)
    return (float(np.percentile(d,2.5)), float(np.percentile(d,97.5)), float(d.std()))

# ---------- interaction (descriptive) ----------
def ols_b3(rows, ycol='h1', center=None, moderator_key='dup_frac'):
    r=[x for x in rows if x.get(ycol) is not None]
    if len(r)<4: return None
    y=np.array([x[ycol] for x in r],float)
    A=np.array([x['A'] for x in r],float)
    S=np.array([x[moderator_key] for x in r],float)
    if center is None: center=float(np.median(S))
    Sc=S-center
    X=np.column_stack([np.ones(len(y)),A,Sc,A*Sc])
    beta,_,_,_=np.linalg.lstsq(X,y,rcond=None)
    return float(beta[3])

# ---------- Wilson & Newcombe ----------
def wilson(k,n,z=1.96):
    if n==0: return (None,None)
    p=k/n; d=1+z*z/n
    c=(p+z*z/(2*n))/d
    hw=(z/d)*np.sqrt(p*(1-p)/n+z*z/(4*n*n))
    return (max(0,c-hw),min(1,c+hw))

def newcombe_diff(k1,n1,k0,n0,z=1.96):
    """Newcombe method 10 for difference of proportions p1-p0."""
    p1=k1/n1; p0=k0/n0
    l1,u1=wilson(k1,n1,z); l0,u0=wilson(k0,n0,z)
    lo=(p1-p0)-np.sqrt((p1-l1)**2+(u0-p0)**2)
    hi=(p1-p0)+np.sqrt((u1-p1)**2+(p0-l0)**2)
    return (p1-p0, lo, hi)

def main():
    fd,od=sys.argv[1],sys.argv[2]
    os.makedirs(od,exist_ok=True)
    ev=load_jsonl(os.path.join(fd,'events.jsonl'))
    rows=join_h3(ev)
    valid=[x for x in rows if not x['infra'] and x.get('h1') is not None]
    grades=json.load(open(os.path.join(fd,'grade_report.json')))
    resolved=set(grades.get('resolved_ids',[]))

    # ===== policy values: unnormalized (old), Hajek (new), DR crossfit (new) =====
    def unnorm_ipw(rows,pi,p=0.5):
        return float(np.mean([(1.0/p if x['A']==pi(x) else 0.0)*x['h1'] for x in rows]))
    pis={'pi_keep':lambda x:0,'pi_static':lambda x:1,
         'pi_signal':lambda x:1 if x['dup_frac']>DUP_THRESHOLD else 0}
    pv={}
    for name,pi in pis.items():
        pv[name]={'unnorm_ipw':unnorm_ipw(valid,pi),
                  'hajek_ipw':hajek_ipw(valid,pi),
                  'dr_crossfit':dr_crossfit(valid,pi),'n':len(valid)}
    # differences with CI: signal vs each static, using Hajek and DR
    pdiff={}
    for est_name,est in [('hajek_ipw',hajek_ipw),('dr_crossfit',dr_crossfit)]:
        for base in ['pi_keep','pi_static']:
            lo,hi,sd=repo_bootstrap_policy_diff(valid,pis['pi_signal'],pis[base],est)
            pdiff[f'signal_minus_{base}__{est_name}']={
                'point':(pv['pi_signal'][est_name]-pv[base][est_name]),
                'repo_boot_ci95':[lo,hi],'se':sd}
    # best static per estimator
    best_static={}
    for est_name in ['unnorm_ipw','hajek_ipw','dr_crossfit']:
        best_static[est_name]='pi_keep' if pv['pi_keep'][est_name]<pv['pi_static'][est_name] else 'pi_static'
    pv['best_static_by_estimator']=best_static
    pv['estimators_agree_on_best_static']=len(set(best_static.values()))==1
    pv['note']=('Hajek self-normalized IPW is the primary policy estimator. Lower cost=better. '
                'Unnormalized HT IPW is reported only to show the finite-N weight artifact at 7/6 split.')
    json.dump(pv,open(os.path.join(od,'policy_value_corrected.json'),'w'),indent=1)

    # ===== placebo distribution (>=5000) + block randomization test =====
    b3_real=ols_b3(valid,'h1')
    center=float(np.median([x['dup_frac'] for x in valid]))
    placebo_b3=[]
    for j in range(N_PLACEBO):
        # deterministic placebo moderator per task
        pv_map={}
        for x in valid:
            h=hashlib.sha256(f"{x['task_id']}|placebo|{j}".encode()).hexdigest()
            pv_map[x['task_id']]=(int(h[:8],16)%10000)/10000.0
        rr=[dict(x, _pl=pv_map[x['task_id']]) for x in valid]
        b=ols_b3(rr,'h1',moderator_key='_pl')
        if b is not None: placebo_b3.append(b)
    placebo_b3=np.array(placebo_b3)
    pct=float((np.sum(np.abs(placebo_b3)>=abs(b3_real))+1)/(len(placebo_b3)+1))
    # block-respecting treatment permutation test for the REAL interaction
    rng=np.random.default_rng(SEED)
    blocks=[f"{x['stratum']}:{x['block_id']}" for x in valid]
    perm_b3=[]
    for _ in range(N_PLACEBO):
        rr=[dict(x) for x in valid]
        for b in set(blocks):
            idx=[i for i,bl in enumerate(blocks) if bl==b]
            perm=rng.permutation([rr[i]['A'] for i in idx])
            for k,i in enumerate(idx): rr[i]['A']=int(perm[k])
        bb=ols_b3(rr,'h1'); 
        if bb is not None: perm_b3.append(bb)
    perm_b3=np.array(perm_b3)
    perm_p=float((np.sum(np.abs(perm_b3)>=abs(b3_real))+1)/(len(perm_b3)+1))
    placebo={'b3_real':b3_real,'center_dup_frac':center,
             'n_placebo':int(len(placebo_b3)),
             'placebo_abs_ge_real_pct':pct,
             'placebo_b3_quantiles':{q:float(np.percentile(placebo_b3,q)) for q in [1,5,25,50,75,95,99]},
             'placebo_b3_abs_quantiles':{q:float(np.percentile(np.abs(placebo_b3),q)) for q in [50,90,95,99]},
             'block_perm_test':{'n':int(len(perm_b3)),'p_two_sided':perm_p,
                'quantiles':{q:float(np.percentile(perm_b3,q)) for q in [2.5,50,97.5]}},
             'interpretation':('The real interaction |b3| is at the '+f'{pct*100:.1f}'+
                'th pct of the placebo-moderator distribution and block-permutation p='+f'{perm_p:.3f}'+
                '. It is NOT distinguishable from finite-sample placebo variation.' if (pct>0.05 and perm_p>0.05)
                else 'The real interaction exceeds finite-sample placebo variation.')}
    json.dump(placebo,open(os.path.join(od,'placebo_distribution.json'),'w'),indent=1)

    # ===== quality: risk difference + Newcombe/Wilson =====
    ld=[x for x in valid if x['A']==1]; noop=[x for x in valid if x['A']==0]
    k1=sum(1 for x in ld if x['task_id'] in resolved); n1=len(ld)
    k0=sum(1 for x in noop if x['task_id'] in resolved); n0=len(noop)
    rd,rlo,rhi=newcombe_diff(k1,n1,k0,n0)
    quality={'LINEDEDUP_resolved':f'{k1}/{n1}','NO_OP_resolved':f'{k0}/{n0}',
             'risk_difference_LINEDEDUP_minus_NOOP':rd,
             'newcombe_ci95':[rlo,rhi],
             'wilson_LINEDEDUP':wilson(k1,n1),'wilson_NO_OP':wilson(k0,n0),
             'verdict':'UNDERPOWERED',
             'note':'No preregistered non-inferiority margin. No catastrophic collapse observed (descriptive), but non-inferiority/safety NOT established.'}

    recon={'study':'Study 1 (N=13 formal pilot)',
           'raw_hashes':{f:sha256_full(os.path.join(fd,f)) for f in
                ['events.jsonl','randomization_state.jsonl','task_state.jsonl','task_grades.json','grade_report.json']},
           'n_valid':len(valid),'b3_real':b3_real,
           'policy_summary':pv,'policy_diffs':pdiff,
           'placebo_summary':{'pct':pct,'block_perm_p':perm_p},
           'quality':quality,
           'label':'Protocol-valid, underpowered formal pilot / Study 1',
           'verdicts':{
             'REDUNDANCY_CAUSAL_MODERATOR':'UNDERPOWERED / NOT_ESTABLISHED',
             'SIGNAL_POLICY_VALUE':'NOT SUPPORTED BY CURRENT POINT ESTIMATES; CONFIRMATORY POLICY EVALUATION UNDERPOWERED',
             'QUALITY_GUARDRAIL':'UNDERPOWERED',
             'PREFIX_BYTE_PRESERVATION':'SUPPORTED BY SOFTWARE INVARIANT',
             'CACHE_COST_EFFECT':'DIRECTIONAL / UNDERPOWERED'}}
    json.dump(recon,open(os.path.join(od,'study1_reconciliation.json'),'w'),indent=1)
    print(json.dumps({'policy_values':{k:{kk:round(vv,1) for kk,vv in v.items() if isinstance(vv,float)} for k,v in pv.items() if isinstance(v,dict)},
                      'best_static_by_estimator':best_static,
                      'estimators_agree':pv['estimators_agree_on_best_static'],
                      'placebo_pct':pct,'block_perm_p':perm_p,'b3_real':round(b3_real,1),
                      'quality_rd':rd,'quality_ci':[rlo,rhi]},indent=1))

if __name__=='__main__': main()
