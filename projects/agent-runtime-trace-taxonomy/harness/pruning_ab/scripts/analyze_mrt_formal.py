#!/usr/bin/env python3
"""MRT Formal — primary analysis + robustness + controller value.
Reads ONLY immutable raw artifacts (events.jsonl, randomization_state.jsonl, task_grades).
numpy-only (no scipy/statsmodels): OLS via lstsq, bootstrap + block-permutation inference.
Lower effective cost is better. All outputs machine-readable JSON + auto-derived report numbers.

Usage: analyze_mrt_formal.py <formal_dir> <out_dir> [--include-pilot <pilot_events.jsonl>]
The primary estimand uses ONLY the formal_locked events. Pilot data is excluded by default.
"""
import json, sys, os, hashlib, collections, argparse
import numpy as np

SEED = 20260701
DUP_THRESHOLD = 0.40   # frozen stratum + pi_signal threshold
H1_WEIGHTS = dict(input=1.0, cache_read=0.1, cache_creation=1.25, output=5.0)

def load_jsonl(path):
    if not os.path.exists(path): return []
    return [json.loads(l) for l in open(path) if l.strip()]

def sha16(path):
    return hashlib.sha256(open(path,'rb').read()).hexdigest()[:16] if os.path.exists(path) else None

# ---------- H=3 joining (mirrors frozen join_h3_outcomes.py) ----------
def join_h3(events):
    by_task = collections.defaultdict(list)
    for e in events:
        if e.get("task_id"): by_task[e["task_id"]].append(e)
    rows=[]
    for tid, evs in by_task.items():
        evs.sort(key=lambda e: e.get("call_index",0))
        exp=[e for e in evs if e.get("experimental_event")]
        if not exp: continue
        iv=exp[0]
        after=[e for e in evs if e.get("call_index",0)>=iv.get("call_index",0)]
        horizon=after[:3]
        h1=iv.get("effective_cost_h1")
        costs=[e.get("effective_cost_h1") for e in horizon if e.get("effective_cost_h1") is not None]
        infra=any(e.get("infrastructure_failure") for e in horizon)
        rows.append(dict(
            task_id=tid, repo=iv.get("repo",""),
            assignment=iv.get("assignment"), A=1 if iv.get("assignment")=="LINEDEDUP" else 0,
            stratum=iv.get("moderator_stratum"),
            dup_frac=iv.get("duplicate_line_fraction",0.0),
            dup_count=iv.get("duplicate_line_count",0),
            seg_chars=iv.get("segment_chars",0),
            calls_so_far=iv.get("call_index",0),
            block_id=iv.get("block_id"), block_position=iv.get("block_position"),
            chars_removed=iv.get("characters_removed",0),
            actual_changed=iv.get("actual_changed",False),
            h1=h1, h3=sum(costs) if costs else None, h3_horizon=len(costs),
            input_tokens=iv.get("input_tokens"), cache_read=iv.get("cache_read_tokens"),
            cache_creation=iv.get("cache_creation_tokens"), output_tokens=iv.get("output_tokens"),
            infra_fail=infra,
        ))
    return rows

# ---------- estimators ----------
def diff_in_means(y, A):
    y=np.asarray(y,float); A=np.asarray(A)
    t=y[A==1]; c=y[A==0]
    if len(t)==0 or len(c)==0: return None
    return float(t.mean()-c.mean())

def boot_ci(y, A, stat=diff_in_means, B=5000, seed=SEED, cluster=None):
    rng=np.random.default_rng(seed)
    y=np.asarray(y,float); A=np.asarray(A)
    ests=[]
    n=len(y)
    if cluster is None:
        for _ in range(B):
            idx=rng.integers(0,n,n)
            s=stat(y[idx],A[idx])
            if s is not None: ests.append(s)
    else:
        cl=np.asarray(cluster); groups=list(set(cl))
        for _ in range(B):
            pick=rng.choice(groups,len(groups),replace=True)
            idx=np.concatenate([np.where(cl==g)[0] for g in pick]) if len(groups)>0 else np.arange(n)
            s=stat(y[idx],A[idx])
            if s is not None: ests.append(s)
    if not ests: return (None,None,None)
    ests=np.array(ests)
    return (float(np.percentile(ests,2.5)), float(np.percentile(ests,97.5)), float(ests.std()))

def block_permutation_p(y, A, blocks, obs_stat, B=10000, seed=SEED):
    """Permute A within blocks; two-sided p for |diff_in_means|."""
    rng=np.random.default_rng(seed)
    y=np.asarray(y,float); A=np.asarray(A); blocks=np.asarray(blocks)
    count=0; total=0
    for _ in range(B):
        Aperm=A.copy()
        for b in set(blocks.tolist()):
            m=blocks==b
            Aperm[m]=rng.permutation(A[m])
        s=diff_in_means(y,Aperm)
        if s is None: continue
        total+=1
        if abs(s)>=abs(obs_stat)-1e-12: count+=1
    return (count+1)/(total+1) if total>0 else None

def ols(X, y):
    """Return beta, and HC0 robust SE."""
    X=np.asarray(X,float); y=np.asarray(y,float)
    beta,_,_,_=np.linalg.lstsq(X,y,rcond=None)
    resid=y-X@beta
    XtX_inv=np.linalg.pinv(X.T@X)
    # HC0
    S=(X*resid[:,None])
    meat=S.T@S
    cov=XtX_inv@meat@XtX_inv
    se=np.sqrt(np.diag(cov))
    return beta, se

def interaction_model(rows, ycol='h1', center=None):
    r=[x for x in rows if x.get(ycol) is not None]
    if len(r)<4: return None
    y=np.array([x[ycol] for x in r],float)
    A=np.array([x['A'] for x in r],float)
    S=np.array([x['dup_frac'] for x in r],float)
    if center is None: center=float(np.median(S))
    Sc=S-center
    # Y = b0 + b1*A + b2*Sc + b3*A*Sc  (block FE omitted at tiny N; report simple + note)
    X=np.column_stack([np.ones(len(y)), A, Sc, A*Sc])
    beta,se=ols(X,y)
    names=['b0_intercept','b1_A','b2_S','b3_AxS']
    return dict(n=len(r), center=center,
                coefs={names[i]:float(beta[i]) for i in range(4)},
                robust_se={names[i]:float(se[i]) for i in range(4)})

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('formal_dir'); ap.add_argument('out_dir')
    ap.add_argument('--events', default=None)
    ap.add_argument('--grades', default=None)
    a=ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)
    ev_path=a.events or os.path.join(a.formal_dir,'events.jsonl')
    events=load_jsonl(ev_path)
    rows=join_h3(events)
    grades={}
    if a.grades and os.path.exists(a.grades):
        gd=json.load(open(a.grades))
        for iid in gd.get('resolved_ids',[]): grades[iid]='resolved'
        for iid in gd.get('unresolved_ids',[]): grades[iid]='unresolved'
    for x in rows: x['resolved']=1 if grades.get(x['task_id'])=='resolved' else (0 if x['task_id'] in grades else None)

    # exclude infra failures (missing-data rule)
    excluded=[x for x in rows if x['infra_fail']]
    valid=[x for x in rows if not x['infra_fail']]

    out={'n_events_total':len(events),
         'n_interventions':len(rows),
         'n_excluded_infra':len(excluded),
         'n_valid':len(valid),
         'events_sha16':sha16(ev_path)}

    if len(valid)>=2:
        A=[x['A'] for x in valid]
        out['assignment_counts']={'LINEDEDUP':int(sum(A)),'NO_OP':int(len(A)-sum(A))}
        out['strata_counts']=dict(collections.Counter(x['stratum'] for x in valid))
        out['repos']=sorted(set(x['repo'] for x in valid))
        out['n_repos']=len(out['repos'])
        out['activation_rate']=float(np.mean([1 if x['actual_changed'] else 0 for x in valid if x['A']==1])) if sum(A)>0 else None

        # ---------- ATE H1 / H3 ----------
        for hc in ['h1','h3']:
            r=[x for x in valid if x.get(hc) is not None]
            if len(r)>=2 and len(set(x['A'] for x in r))==2:
                y=[x[hc] for x in r]; Aa=[x['A'] for x in r]
                blk=[f"{x['stratum']}:{x['block_id']}" for x in r]
                cl=[x['repo'] for x in r]
                d=diff_in_means(y,Aa)
                lo,hi,sd=boot_ci(y,Aa)
                clo,chi,csd=boot_ci(y,Aa,cluster=cl)
                pp=block_permutation_p(y,Aa,blk,d)
                out[f'ATE_{hc}']=dict(n=len(r), estimate_LINEDEDUP_minus_NOOP=d,
                    boot_ci95=[lo,hi], boot_se=sd,
                    repo_cluster_ci95=[clo,chi], repo_cluster_se=csd,
                    block_perm_p=pp,
                    mean_LINEDEDUP=float(np.mean([x[hc] for x in r if x['A']==1])),
                    mean_NOOP=float(np.mean([x[hc] for x in r if x['A']==0])))
            else:
                out[f'ATE_{hc}']=dict(n=len(r), note='insufficient support (need both arms)')

        # ---------- interaction b3 ----------
        im=interaction_model(valid,'h1')
        out['interaction_h1']=im
        im3=interaction_model(valid,'h3')
        out['interaction_h3']=im3

        # ---------- CATE by stratum ----------
        out['CATE']={}
        for st in ['HIGH_REDUNDANCY','MIXED_REDUNDANCY']:
            r=[x for x in valid if x['stratum']==st and x.get('h1') is not None]
            if len(r)>=2 and len(set(x['A'] for x in r))==2:
                y=[x['h1'] for x in r]; Aa=[x['A'] for x in r]
                d=diff_in_means(y,Aa); lo,hi,sd=boot_ci(y,Aa)
                out['CATE'][st]=dict(n=len(r), estimate=d, boot_ci95=[lo,hi])
            else:
                out['CATE'][st]=dict(n=len(r), note='insufficient support')
        if all(out['CATE'].get(s,{}).get('estimate') is not None for s in ['HIGH_REDUNDANCY','MIXED_REDUNDANCY']):
            out['CATE']['high_minus_mixed']=out['CATE']['HIGH_REDUNDANCY']['estimate']-out['CATE']['MIXED_REDUNDANCY']['estimate']

        # ---------- mechanism decomposition ----------
        out['mechanism']={}
        for comp in ['input_tokens','cache_read','cache_creation','output_tokens']:
            r=[x for x in valid if x.get(comp) is not None]
            if len(r)>=2 and len(set(x['A'] for x in r))==2:
                out['mechanism'][comp]=dict(
                    mean_LINEDEDUP=float(np.mean([x[comp] for x in r if x['A']==1])),
                    mean_NOOP=float(np.mean([x[comp] for x in r if x['A']==0])),
                    diff=diff_in_means([x[comp] for x in r],[x['A'] for x in r]))

        # ---------- controller policy values (IPW, propensity=0.5) ----------
        # V(pi) = mean over events of [1{A==pi(s)} / p(A)] * (-cost)   [negate: higher value=lower cost]
        # DR with outcome model = stratum mean.
        def policy_value(rows_h, pi_fn):
            # IPW
            ipw=[]; dr=[]
            # outcome model: mean cost by (assignment, stratum)
            om={}
            for st in set(x['stratum'] for x in rows_h):
                for aa in [0,1]:
                    vals=[x['h1'] for x in rows_h if x['stratum']==st and x['A']==aa]
                    om[(st,aa)]=np.mean(vals) if vals else None
            for x in rows_h:
                a_star=pi_fn(x)
                p=0.5
                # IPW estimate of cost under pi
                ind=1.0 if x['A']==a_star else 0.0
                ipw.append(ind/p * x['h1'])
                # DR
                mhat=om.get((x['stratum'],a_star))
                if mhat is None: mhat=x['h1']
                dr.append(mhat + ind/p*(x['h1']-om.get((x['stratum'],x['A']),x['h1'])))
            return dict(ipw_cost=float(np.mean(ipw)), dr_cost=float(np.mean(dr)), n=len(rows_h))
        rh=[x for x in valid if x.get('h1') is not None]
        if len(rh)>=2:
            out['controller']={
                'pi_keep':   policy_value(rh, lambda x:0),
                'pi_static': policy_value(rh, lambda x:1),
                'pi_signal': policy_value(rh, lambda x:1 if x['dup_frac']>DUP_THRESHOLD else 0),
                'note':'IPW+DR, propensity=0.5, lower cost=better. Small N: interpret as effect-size not significance.'
            }

        # ---------- robustness: threshold sensitivity, horizon, leave-top-k ----------
        out['robustness']={}
        # threshold sensitivity for pi_signal
        if len(rh)>=2:
            out['robustness']['threshold_sensitivity']={}
            for th in [0.30,0.40,0.50]:
                out['robustness']['threshold_sensitivity'][str(th)]=policy_value(rh, lambda x,t=th:1 if x['dup_frac']>t else 0)
        # leave-top-k on |h1|
        if len([x for x in valid if x.get('h1') is not None])>=4:
            srt=sorted([x for x in valid if x.get('h1') is not None], key=lambda x:-abs(x['h1']))
            out['robustness']['leave_top_k']={}
            for k in [1,3,5]:
                sub=srt[k:]
                if len(sub)>=2 and len(set(x['A'] for x in sub))==2:
                    out['robustness']['leave_top_k'][f'k={k}']=diff_in_means([x['h1'] for x in sub],[x['A'] for x in sub])
        # leave-one-repo-out
        out['robustness']['leave_one_repo_out']={}
        for rp in set(x['repo'] for x in valid):
            sub=[x for x in valid if x['repo']!=rp and x.get('h1') is not None]
            if len(sub)>=2 and len(set(x['A'] for x in sub))==2:
                out['robustness']['leave_one_repo_out'][f'drop_{rp}']=diff_in_means([x['h1'] for x in sub],[x['A'] for x in sub])
        # placebo moderators: task-id hash, event-id hash
        out['robustness']['placebo']={}
        for x in valid:
            x['_taskhash']=(int(hashlib.sha256(x['task_id'].encode()).hexdigest(),16)%1000)/1000.0
        im_placebo=interaction_model([dict(x, dup_frac=x['_taskhash']) for x in valid],'h1')
        out['robustness']['placebo']['taskid_hash_interaction']=im_placebo['coefs']['b3_AxS'] if im_placebo else None

    else:
        out['note']='fewer than 2 valid interventions — analysis not computable; report N and eligibility only'

    json.dump(out, open(os.path.join(a.out_dir,'analysis_output.json'),'w'), indent=1)
    # also write the joined rows (immutable-derived)
    json.dump(rows, open(os.path.join(a.out_dir,'joined_rows.json'),'w'), indent=1)
    print(json.dumps({k:out[k] for k in out if k in
          ('n_events_total','n_interventions','n_valid','assignment_counts','strata_counts','n_repos')}, indent=1))

if __name__=='__main__':
    main()
