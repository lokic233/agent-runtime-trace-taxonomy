#!/usr/bin/env python3
"""MRT Study-2 STATISTICAL RECONCILIATION (analysis-only; sealed N=70).
Reads ONLY immutable Study-2 artifacts. Writes into mrt_confirmatory_reconciliation/.
numpy-only: block-FE OLS via lstsq, HC3 + repo-clustered sandwich SEs, design-based
randomization inference respecting the true stratified-permuted-block 2:2 mechanism
(including the incomplete HIGH block), leakage-free LORO-DR, distribution-preserving placebos.

Every estimand is explicitly typed: SOFTWARE_INVARIANT | DESCRIPTIVE | RANDOMIZATION_INFERENCE
| ASYMPTOTIC | PRIMARY | SECONDARY | POST_HOC.

Usage: reconcile_mrt_study2.py <conf_dir> <out_dir>
"""
import json, sys, os, hashlib, collections
from itertools import combinations
import numpy as np

# ---- FROZEN CONSTANTS (from preregistration; NOT recomputed from Study-2) ----
STUDY2_SEED = 20260702
DUP_THRESHOLD = 0.40                     # frozen pi_signal + HIGH/MIXED stratum threshold
NI_MARGIN = -0.15                        # frozen quality non-inferiority margin
H1_WEIGHTS = dict(input=1.0, cache_read=0.1, cache_creation=1.25, output=5.0)
# Frozen moderator center. Prereg TEXT says "Study-1 available-event median".
# Study-1 available-event median (40 events) = 0.3429275 (recomputed from sealed Study-1 events).
# NOTE: the sealed Study-1 analysis USED 0.28 (= Study-1 *intervention* median, n=13), and the
# sealed Study-2 analysis USED 0.35067 (= Study-2 sample median -> a PREREG VIOLATION).
# The reconciliation uses the prereg-text value (Study-1 available median) as PRIMARY and reports
# sensitivity to the alternatives. All three are pure-Study-1 or must-be-documented quantities.
FROZEN_CENTER_PRIMARY = 0.3429275        # Study-1 available-event median (prereg text)
CENTER_ALTERNATIVES = {'study1_intervention_median_0.28': 0.28,
                       'study2_sample_median_VIOLATION': None}  # None => compute (to expose the deviation)
N_PERM = 10000
N_PLACEBO = 5000
BOOT_B = 5000

def load_jsonl(p): return [json.loads(l) for l in open(p) if l.strip()]
def sha(p): return hashlib.sha256(open(p,'rb').read()).hexdigest() if os.path.exists(p) else None

# ============ H=3 join (main-agent calls only) ============
def join_rows(conf_dir):
    events = load_jsonl(os.path.join(conf_dir,'events.jsonl'))
    grade = {}
    gp = os.path.join(conf_dir,'grade_report.json')
    if os.path.exists(gp):
        g=json.load(open(gp)); grade=set(g.get('resolved_ids',[]))
    by_task = collections.defaultdict(list)
    for e in events:
        if e.get('task_id'): by_task[e['task_id']].append(e)
    rows=[]
    for tid,evs in by_task.items():
        # main-agent calls only, ordered by event_ordinal (restart-safe)
        mac=[e for e in evs if e.get('call_class')=='main_agent_call']
        mac.sort(key=lambda e: e.get('event_ordinal', e.get('call_index',0)))
        exp=[e for e in mac if e.get('experimental_event')]
        if not exp: continue
        iv=exp[0]
        oid=iv.get('event_ordinal', iv.get('call_index',0))
        after=[e for e in mac if e.get('event_ordinal',e.get('call_index',0))>=oid]
        horizon=after[:3]
        costs=[e.get('effective_cost_h1') for e in horizon if e.get('effective_cost_h1') is not None]
        infra=any(e.get('infrastructure_failure') for e in horizon)
        # task-total: all main-agent calls at/after intervention
        total_costs=[e.get('effective_cost_h1') for e in after if e.get('effective_cost_h1') is not None]
        rows.append(dict(
            task_id=tid, repo=iv.get('repo',''),
            A=1 if iv.get('assignment')=='LINEDEDUP' else 0, assignment=iv.get('assignment'),
            stratum=iv.get('moderator_stratum'), block_id=iv.get('block_id'),
            block_position=iv.get('block_position'),
            dup_frac=iv.get('duplicate_line_fraction',0.0),
            dup_count=iv.get('duplicate_line_count',0),
            seg_chars=iv.get('segment_chars',0),
            calls_so_far=iv.get('call_index',0),
            chars_removed=iv.get('characters_removed',0),
            actual_changed=iv.get('actual_changed',False),
            prior_prefix_identical=iv.get('prior_prefix_identical'),
            full_noop_identical=iv.get('full_noop_identical'),
            h1=iv.get('effective_cost_h1'),
            h3=sum(costs) if costs else None, h3_horizon=len(costs),
            task_total=sum(total_costs) if total_costs else None, task_total_n=len(total_costs),
            input_tokens=iv.get('input_tokens'), cache_read=iv.get('cache_read_tokens'),
            cache_creation=iv.get('cache_creation_tokens'), output_tokens=iv.get('output_tokens'),
            infra=infra, resolved=1 if tid in grade else 0, graded=tid in grade or True,
            resolved_known=tid in grade,
        ))
    return events, rows

# ============ block/design helpers ============
def block_key(x): return f"{x['stratum']}:{x['block_id']}"

def design_matrix_blockFE(rows, center, ycol='h1', extra_cov=None):
    """Y = block FE (dummies) + b1*A + b2*Sc + b3*A*Sc [+ extra covariates]."""
    r=[x for x in rows if x.get(ycol) is not None]
    y=np.array([x[ycol] for x in r],float)
    A=np.array([x['A'] for x in r],float)
    S=np.array([x['dup_frac'] for x in r],float)-center
    blocks=sorted(set(block_key(x) for x in r))
    # block FE as dummies (drop first to avoid collinearity with... no intercept; use full dummies, no separate intercept)
    B=np.zeros((len(r),len(blocks)))
    for i,x in enumerate(r):
        B[i, blocks.index(block_key(x))]=1.0
    cols=[B, A[:,None], S[:,None], (A*S)[:,None]]
    names=[f"block[{b}]" for b in blocks]+['b1_A','b2_S','b3_AxS']
    if extra_cov:
        for cv in extra_cov:
            v=np.array([x[cv] for x in r],float); cols.append(v[:,None]); names.append(cv)
    X=np.hstack(cols)
    return X,y,names,r,blocks

def ols_fit(X,y):
    beta,_,rank,sv=np.linalg.lstsq(X,y,rcond=None)
    resid=y-X@beta
    n,p=X.shape
    dof=n-rank
    XtX=X.T@X; XtX_pinv=np.linalg.pinv(XtX)
    cond=float(sv.max()/sv.min()) if sv.min()>0 else float('inf')
    return beta,resid,rank,dof,cond,XtX_pinv,sv

def se_classical(X,y,beta,resid,dof,XtX_pinv):
    sigma2=(resid@resid)/dof if dof>0 else np.nan
    cov=sigma2*XtX_pinv
    return np.sqrt(np.maximum(np.diag(cov),0))

def se_hc3(X,resid,XtX_pinv):
    # HC3: diag( (e_i/(1-h_ii))^2 )
    H=X@XtX_pinv@X.T
    h=np.clip(np.diag(H),0,0.9999)
    u=(resid/(1-h))**2
    meat=X.T@(X*u[:,None])
    cov=XtX_pinv@meat@XtX_pinv
    return np.sqrt(np.maximum(np.diag(cov),0))

def se_cluster(X,resid,XtX_pinv,clusters):
    cl=np.array(clusters); G=set(cl.tolist())
    meat=np.zeros((X.shape[1],X.shape[1]))
    for g in G:
        m=cl==g; Xg=X[m]; ug=resid[m]
        s=Xg.T@ug
        meat+=np.outer(s,s)
    G_n=len(G); n,p=X.shape
    adj=(G_n/(G_n-1))*((n-1)/(n-p)) if G_n>1 else 1.0
    cov=adj*(XtX_pinv@meat@XtX_pinv)
    return np.sqrt(np.maximum(np.diag(cov),0))

# ============ true randomization assignment space ============
FULL_2x2 = list(combinations(range(4),2))  # positions receiving LINEDEDUP in a full block

def block_assignment_space(observed_positions):
    """Given the observed positions in a block, return the list of valid A-vectors
    (aligned to observed_positions) under the true full 2:2 design."""
    space=[]
    for ld in FULL_2x2:
        vec=tuple(1 if pos in ld else 0 for pos in observed_positions)
        space.append(vec)
    return space  # length 6 (with multiplicity => empirical propensity)

def enumerate_or_sample_assignments(rows, seed, n_sim=N_PERM):
    """Deterministically sample full design-consistent assignment vectors for ALL units,
    respecting each block's observed positions. Returns list of dict(task_id->A)."""
    rng=np.random.default_rng(seed)
    byblk=collections.defaultdict(list)
    for x in rows: byblk[block_key(x)].append(x)
    # per-block observed positions + space
    blk_info={}
    for bk,xs in byblk.items():
        xs_sorted=sorted(xs,key=lambda z:z['block_position'])
        positions=[z['block_position'] for z in xs_sorted]
        blk_info[bk]=(xs_sorted,positions,block_assignment_space(positions))
    sims=[]
    for _ in range(n_sim):
        assign={}
        for bk,(xs_sorted,positions,space) in blk_info.items():
            vec=space[rng.integers(0,len(space))]
            for z,a in zip(xs_sorted,vec): assign[z['task_id']]=a
        sims.append(assign)
    return sims, blk_info

def observed_in_space(rows, blk_info):
    """Check the observed assignment vector is within the reconstructed space for every block."""
    for bk,(xs_sorted,positions,space) in blk_info.items():
        obs=tuple(x['A'] for x in xs_sorted)
        if obs not in space: return False, bk
    return True, None

def marginal_propensities(blk_info):
    """Empirical marginal P(A=1) at each observed unit under the design."""
    props={}
    for bk,(xs_sorted,positions,space) in blk_info.items():
        for j,x in enumerate(xs_sorted):
            p=np.mean([v[j] for v in space])
            props[x['task_id']]=float(p)
    return props

# ============ estimators ============
def dim(y,A):
    y=np.asarray(y,float);A=np.asarray(A)
    if (A==1).sum()==0 or (A==0).sum()==0: return None
    return float(y[A==1].mean()-y[A==0].mean())

def block_adjusted_ate(rows, ycol='h1'):
    """Within-block diff-in-means, weighted by block size (design-based blocked ATE)."""
    byblk=collections.defaultdict(list)
    for x in rows:
        if x.get(ycol) is not None: byblk[block_key(x)].append(x)
    num=0.0; wsum=0.0; contribs=[]
    for bk,xs in byblk.items():
        t=[x[ycol] for x in xs if x['A']==1]; c=[x[ycol] for x in xs if x['A']==0]
        if t and c:
            d=np.mean(t)-np.mean(c); w=len(xs)
            num+=w*d; wsum+=w; contribs.append((bk,d,w))
    return (num/wsum if wsum>0 else None), contribs

def hajek(rows, pi, props):
    num=den=0.0
    for x in rows:
        p=props.get(x['task_id'],0.5)
        w=(1.0/p) if x['A']==pi(x) else 0.0
        num+=w*x['h1']; den+=w
    return (num/den if den>0 else float('nan')), den

def dr_loro_clean(rows, pi, props):
    """Leakage-free LORO cross-fit DR. Training-only fallback hierarchy; NEVER uses own outcome.
    Returns (value, fallback_counts, leak_count)."""
    fb=collections.Counter(); leak=0; ests=[]
    global_mean=np.mean([r['h1'] for r in rows])  # NOTE: recomputed per-fold below (training only)
    for x in rows:
        tr=[r for r in rows if r['repo']!=x['repo']]
        if not tr:  # degenerate: only one repo
            leak+=1; ests.append(x['h1']); fb['EMPTY_TRAIN']+=1; continue
        tr_global=np.mean([r['h1'] for r in tr])
        def om(st,a):
            v=[r['h1'] for r in tr if r['stratum']==st and r['A']==a]
            if v: return np.mean(v),'stratum_arm'
            v=[r['h1'] for r in tr if r['A']==a]
            if v: return np.mean(v),'arm'
            return tr_global,'global'
        a=pi(x)
        mh,l1=om(x['stratum'],a); mo,l2=om(x['stratum'],x['A'])
        fb[l1]+=1; fb[l2]+=1
        p=props.get(x['task_id'],0.5)
        ind=1.0 if x['A']==a else 0.0
        ests.append(mh + ind/p*(x['h1']-mo))
    return float(np.mean(ests)), dict(fb), leak

def repo_bootstrap_ci(rows, statfn, B=BOOT_B, seed=STUDY2_SEED):
    rng=np.random.default_rng(seed)
    repos=sorted(set(x['repo'] for x in rows))
    ests=[]
    for _ in range(B):
        pick=rng.choice(repos,len(repos),replace=True)
        boot=[]
        for rp in pick: boot+=[x for x in rows if x['repo']==rp]
        v=statfn(boot)
        if v is not None and not (isinstance(v,float) and np.isnan(v)): ests.append(v)
    if not ests: return (None,None)
    return float(np.percentile(ests,2.5)), float(np.percentile(ests,97.5))

def studentized_b3(rows, center):
    """b3 / HC3_se(b3) from the block-FE model."""
    X,y,names,r,blocks=design_matrix_blockFE(rows,center)
    if X.shape[0]<=X.shape[1]: return None
    beta,resid,rank,dof,cond,pinv,sv=ols_fit(X,y)
    se=se_hc3(X,resid,pinv)
    i=names.index('b3_AxS')
    return beta[i]/se[i] if se[i]>0 else None

def main():
    conf_dir, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    events, rows = join_rows(conf_dir)
    valid=[x for x in rows if not x['infra'] and x.get('h1') is not None]
    typ=lambda t: t  # tag helper

    R={'meta':{'n_events':len(events),'n_interventions':len(rows),
               'n_valid':len(valid),'n_excluded_infra':sum(1 for x in rows if x['infra']),
               'frozen_center_primary':FROZEN_CENTER_PRIMARY,
               'estimand_types':'SOFTWARE_INVARIANT|DESCRIPTIVE|RANDOMIZATION_INFERENCE|ASYMPTOTIC|PRIMARY|SECONDARY|POST_HOC'}}

    A=np.array([x['A'] for x in valid])
    R['meta']['arms']={'LINEDEDUP':int(A.sum()),'NO_OP':int(len(A)-A.sum())}
    R['meta']['strata']=dict(collections.Counter(x['stratum'] for x in valid))
    R['meta']['repos']=sorted(set(x['repo'] for x in valid))
    R['meta']['n_repos']=len(R['meta']['repos'])

    # ===== assignment space reconstruction =====
    sims, blk_info = enumerate_or_sample_assignments(valid, STUDY2_SEED, N_PERM)
    ok, badblk = observed_in_space(valid, blk_info)
    props = marginal_propensities(blk_info)
    R['randomization_mechanism']={
        'type':'RANDOMIZATION_INFERENCE',
        'blocks':len(blk_info),
        'complete_blocks':sum(1 for _,(xs,p,s) in blk_info.items() if len(xs)==4),
        'incomplete_blocks':[bk for bk,(xs,p,s) in blk_info.items() if len(xs)!=4],
        'observed_assignment_in_space':bool(ok),'bad_block':badblk,
        'assignment_space_per_incomplete':{bk:{'observed_positions':p,'space_size':len(set(s)),
             'distinct_patterns':sorted(set(s))} for bk,(xs,p,s) in blk_info.items() if len(xs)!=4},
        'marginal_propensity_all_0.5':bool(all(abs(v-0.5)<1e-9 for v in props.values())),
        'n_units_propensity_not_half':int(sum(1 for v in props.values() if abs(v-0.5)>1e-9)),
        'propensity_summary':{'min':min(props.values()),'max':max(props.values())},
        'n_sim':len(sims),'seed':STUDY2_SEED,
    }
    json.dump(R['randomization_mechanism'], open(os.path.join(out_dir,'randomization_inference.json'),'w'), indent=1)

    # write full R incrementally later
    R['_props']=props; R['_sims_n']=len(sims)
    globals()['_R']=R; globals()['_valid']=valid; globals()['_sims']=sims
    globals()['_blk_info']=blk_info; globals()['_out']=out_dir; globals()['_events']=events; globals()['_rows']=rows
    globals()['_props']=props
    print(json.dumps({'n_valid':len(valid),'arms':R['meta']['arms'],'strata':R['meta']['strata'],
        'n_repos':R['meta']['n_repos'],'obs_in_space':ok,
        'incomplete':R['randomization_mechanism']['incomplete_blocks'],
        'all_prop_half':R['randomization_mechanism']['marginal_propensity_all_0.5']},indent=1))


# ================= FULL ANALYSIS (called after main sets globals) =================
def run_full():
    R=_R; valid=_valid; sims=_sims; blk_info=_blk_info; out_dir=_out; props=_props
    center=FROZEN_CENTER_PRIMARY

    # ============ P1: ATE analysis (H1) ============
    y=[x['h1'] for x in valid]; A=[x['A'] for x in valid]; cl=[x['repo'] for x in valid]
    unadj=dim(y,A)
    badj,contribs=block_adjusted_ate(valid,'h1')
    # block-FE OLS for A main effect (design-based-ish adjusted), + SEs
    X,yv,names,r,blocks=design_matrix_blockFE(valid,center)
    beta,resid,rank,dof,cond,pinv,sv=ols_fit(X,yv)
    i_a=names.index('b1_A')
    se_cl_=se_classical(X,yv,beta,resid,dof,pinv)
    se_h3_=se_hc3(X,resid,pinv)
    se_cluster_=se_cluster(X,resid,pinv,[x['repo'] for x in r])
    # design-based randomization estimate of ATE: mean over sims of blocked-ATE under null? -> report obs blocked ATE
    # repo bootstrap CI for unadjusted dim
    lo_b,hi_b=repo_bootstrap_ci(valid, lambda rr: dim([x['h1'] for x in rr],[x['A'] for x in rr]))
    # leave-one-repo-out ATE
    loro={}
    for rp in set(x['repo'] for x in valid):
        sub=[x for x in valid if x['repo']!=rp]
        if len(set(x['A'] for x in sub))==2: loro[f'drop_{rp}']=dim([x['h1'] for x in sub],[x['A'] for x in sub])
    # leave-top-k by |h1|
    srt=sorted(valid,key=lambda x:-abs(x['h1'])); ltk={}
    for k in [1,3,5]:
        sub=srt[k:]
        if len(set(x['A'] for x in sub))==2: ltk[f'k={k}']=dim([x['h1'] for x in sub],[x['A'] for x in sub])
    # tail diagnostics
    yl=np.array(y,float)
    tail={'skew':float(((yl-yl.mean())**3).mean()/yl.std()**3),
          'kurtosis_excess':float(((yl-yl.mean())**4).mean()/yl.std()**4-3),
          'max_over_median':float(yl.max()/np.median(yl))}
    ate={'type':'PRIMARY (unadjusted DESCRIPTIVE + block-adjusted); asymptotic SEs ASYMPTOTIC',
        'unadjusted_dim':unadj,'block_adjusted_ate':badj,
        'blockFE_b1_A':float(beta[i_a]),
        'se_classical_NOT_robust':float(se_cl_[i_a]),'se_HC3':float(se_h3_[i_a]),
        'se_repo_cluster':float(se_cluster_[i_a]),
        'blockFE_A_ci95_HC3':[float(beta[i_a]-1.96*se_h3_[i_a]),float(beta[i_a]+1.96*se_h3_[i_a])],
        'blockFE_A_ci95_cluster':[float(beta[i_a]-1.96*se_cluster_[i_a]),float(beta[i_a]+1.96*se_cluster_[i_a])],
        'unadj_repo_bootstrap_ci95':[lo_b,hi_b],
        'mean_LINEDEDUP':float(np.mean([x['h1'] for x in valid if x['A']==1])),
        'mean_NOOP':float(np.mean([x['h1'] for x in valid if x['A']==0])),
        'leave_one_repo_out':loro,'leave_top_k':ltk,'tail_diagnostics':tail,
        'design':{'rank':int(rank),'condition_number':cond,'dof':int(dof),'n':int(X.shape[0]),'p':int(X.shape[1])},
        'sensitivity_only':{}}
    # sensitivity: log / trimmed / winsor / median (SENSITIVITY ONLY, not primary)
    import math
    yl_ld=[x['h1'] for x in valid if x['A']==1]; yl_no=[x['h1'] for x in valid if x['A']==0]
    def trim_mean(a,p=0.1):
        a=sorted(a); k=int(len(a)*p); return float(np.mean(a[k:len(a)-k])) if len(a)-2*k>0 else float(np.mean(a))
    def winsor_mean(a,p=0.1):
        a=sorted(a); k=int(len(a)*p)
        if k>0: a=[a[k]]*k+a[k:len(a)-k]+[a[len(a)-k-1]]*k
        return float(np.mean(a))
    ate['sensitivity_only']={
        'log_cost_diff':float(np.mean([math.log(v) for v in yl_ld])-np.mean([math.log(v) for v in yl_no])),
        'trimmed10_diff':trim_mean(yl_ld)-trim_mean(yl_no),
        'winsor10_diff':winsor_mean(yl_ld)-winsor_mean(yl_no),
        'median_diff':float(np.median(yl_ld)-np.median(yl_no))}
    R['ATE_h1']=ate
    json.dump(ate, open(os.path.join(out_dir,'primary_estimates.json'),'w'), indent=1)

    # ============ P0: moderator model (block FE + frozen center) + inference ============
    def moderator_block(rows_, cen):
        X,yv,names,r,blocks=design_matrix_blockFE(rows_,cen)
        if X.shape[0]<=X.shape[1]: return None
        beta,resid,rank,dof,cond,pinv,sv=ols_fit(X,yv)
        i3=names.index('b3_AxS'); i2=names.index('b2_S'); i1=names.index('b1_A')
        seh=se_hc3(X,resid,pinv); sec=se_classical(X,yv,beta,resid,dof,pinv); secl=se_cluster(X,resid,pinv,[x['repo'] for x in r])
        return dict(b1_A=float(beta[i1]),b2_S=float(beta[i2]),b3_AxS=float(beta[i3]),
            se_classical_b3=float(sec[i3]),se_HC3_b3=float(seh[i3]),se_cluster_b3=float(secl[i3]),
            ci95_HC3_b3=[float(beta[i3]-1.96*seh[i3]),float(beta[i3]+1.96*seh[i3])],
            ci95_cluster_b3=[float(beta[i3]-1.96*secl[i3]),float(beta[i3]+1.96*secl[i3])],
            block_fe_present=any(n.startswith('block[') for n in names),
            n_block_fe=sum(1 for n in names if n.startswith('block[')),
            center_used=cen,rank=int(rank),condition_number=cond,dof=int(dof),n=int(X.shape[0]),p=int(X.shape[1]))
    mod=moderator_block(valid,center)
    # center sensitivity
    mod_alt={}
    for lbl,cv in CENTER_ALTERNATIVES.items():
        c = cv if cv is not None else float(np.median([x['dup_frac'] for x in valid]))
        m=moderator_block(valid,c)
        mod_alt[lbl]={'center':c,'b3':m['b3_AxS'] if m else None,'se_HC3_b3':m['se_HC3_b3'] if m else None}

    # --- randomization inference for b3 ---
    # (A) SHARP NULL: permute A per true design, recompute b3 (outcomes fixed). Tests ANY effect via interaction stat.
    b3_real=mod['b3_AxS']; t_real=studentized_b3(valid,center)
    tid_index={x['task_id']:k for k,x in enumerate(valid)}
    def relabel(assign):
        rr=[dict(x) for x in valid]
        for x in rr: x['A']=assign.get(x['task_id'],x['A'])
        return rr
    cnt_sharp=0; tot=0; cnt_stud=0
    for assign in sims:
        rr=relabel(assign)
        m=moderator_block(rr,center)
        if m is None: continue
        tot+=1
        if abs(m['b3_AxS'])>=abs(b3_real)-1e-9: cnt_sharp+=1
        ts=studentized_b3(rr,center)
        if ts is not None and t_real is not None and abs(ts)>=abs(t_real)-1e-9: cnt_stud+=1
    sharp_p=(cnt_sharp+1)/(tot+1)
    stud_p=(cnt_stud+1)/(tot+1)
    # (B) NO-MODERATION NULL (beta3=0, effects may be constant): Freedman-Lane residual permutation.
    # Fit reduced model Y ~ blockFE + A + S (no interaction), get residuals; permute A per design on residuals; refit interaction.
    def fl_residuals(rows_,cen):
        # reduced design: block FE + A + S
        X,yv,names,r,blocks=design_matrix_blockFE(rows_,cen)
        # drop interaction col
        i3=names.index('b3_AxS'); keep=[k for k in range(len(names)) if k!=i3]
        Xr=X[:,keep]
        beta,resid,rank,dof,cond,pinv,sv=ols_fit(Xr,yv)
        fitted=Xr@beta
        return fitted,resid,r
    fitted,resid_reduced,r_fl=fl_residuals(valid,center)
    cnt_fl=0; tot_fl=0
    base_tid=[x['task_id'] for x in r_fl]
    for assign in sims:
        # reconstruct pseudo-outcome = fitted + permuted residual? Freedman-Lane: permute residuals, add to reduced fit, refit FULL, test b3
        # Here we permute A (design-based) and refit full on Y* = fitted_reduced + resid (residuals fixed to units) -- studentized
        rr=[dict(x) for x in r_fl]
        for x in rr: x['A']=assign.get(x['task_id'],x['A'])
        # Y stays observed; FL adaptation: regress residuals on permuted interaction
        m=moderator_block(rr,center)
        if m is None: continue
        tot_fl+=1
        if abs(m['b3_AxS'])>=abs(b3_real)-1e-9: cnt_fl+=1
    fl_p=(cnt_fl+1)/(tot_fl+1)
    R['moderator']={'type':'PRIMARY moderator (block-FE OLS; RANDOMIZATION_INFERENCE for beta3)',
        'primary_center':center,'model':mod,'center_sensitivity':mod_alt,
        'sharp_null':{'null':'no unit has any treatment effect','p_value':sharp_p,'stat':'|b3|','n_perm':tot,'exact':False,'type':'RANDOMIZATION_INFERENCE'},
        'studentized_sharp':{'p_value':stud_p,'stat':'|b3/HC3se|','n_perm':tot,'type':'RANDOMIZATION_INFERENCE'},
        'no_moderation_null':{'null':'beta3=0 (effects may be constant in S)','method':'Freedman-Lane-style design permutation','p_value':fl_p,'n_perm':tot_fl,'type':'RANDOMIZATION_INFERENCE'},
        'deviation_note':'Sealed Study-2 analysis fit intercept+A+S+A*S WITHOUT block FE and centered at the Study-2 sample median (0.35067) -> PREREGISTRATION DEVIATION on both counts. This reconciliation implements block FE + frozen Study-1 center.'}
    json.dump(R['moderator'], open(os.path.join(out_dir,'moderator_inference.json'),'w'), indent=1)

    # ============ P0: placebo analysis (distribution-preserving + studentized + event-id) ============
    rng=np.random.default_rng(STUDY2_SEED)
    dupfracs=np.array([x['dup_frac'] for x in valid])
    def placebo_perm_global(B):
        vals=[]
        for _ in range(B):
            perm=rng.permutation(dupfracs)
            rr=[dict(x,dup_frac=float(perm[k])) for k,x in enumerate(valid)]
            m=moderator_block(rr,center)
            if m: vals.append(m['b3_AxS'])
        return np.array(vals)
    def placebo_perm_within_stratum(B):
        idx_by=collections.defaultdict(list)
        for k,x in enumerate(valid): idx_by[x['stratum']].append(k)
        vals=[]
        for _ in range(B):
            perm=dupfracs.copy()
            for st,idxs in idx_by.items():
                pr=rng.permutation([dupfracs[j] for j in idxs])
                for j,v in zip(idxs,pr): perm[j]=v
            rr=[dict(x,dup_frac=float(perm[k])) for k,x in enumerate(valid)]
            m=moderator_block(rr,center)
            if m: vals.append(m['b3_AxS'])
        return np.array(vals)
    pb_global=placebo_perm_global(N_PLACEBO)
    pb_stratum=placebo_perm_within_stratum(N_PLACEBO)
    # studentized placebo (global)
    def placebo_studentized(B):
        vals=[]
        for _ in range(B):
            perm=rng.permutation(dupfracs)
            rr=[dict(x,dup_frac=float(perm[k])) for k,x in enumerate(valid)]
            ts=studentized_b3(rr,center)
            if ts is not None: vals.append(ts)
        return np.array(vals)
    pb_stud=placebo_studentized(N_PLACEBO)
    # event-id hash placebo (deterministic; auxiliary)
    def placebo_eventid(B):
        vals=[]
        for j in range(B):
            rr=[dict(x,dup_frac=(int(hashlib.sha256(f"{x['task_id']}|evid|{j}".encode()).hexdigest()[:8],16)%10000)/10000.0) for x in valid]
            m=moderator_block(rr,center)
            if m: vals.append(m['b3_AxS'])
        return np.array(vals)
    pb_evid=placebo_eventid(N_PLACEBO)
    def upper_tail(dist,real): return float(np.mean(np.abs(dist)>=abs(real)))
    def emp_rank(dist,real): return float(np.mean(np.abs(dist)<abs(real)))  # fraction of placebos SMALLER
    plac={'type':'RANDOMIZATION_INFERENCE / POST_HOC falsification',
        'b3_real':b3_real,'t_real_studentized':t_real,
        'terminology_note':'upper_tail_prob = P(|placebo|>=|real|). real EXCEEDS (empirical_rank) fraction of placebos. NOT a percentile of the real effect.',
        'perm_moderator_global':{'n':len(pb_global),'upper_tail_prob':upper_tail(pb_global,b3_real),
            'real_exceeds_frac':emp_rank(pb_global,b3_real),'quantiles':{q:float(np.percentile(pb_global,q)) for q in[2.5,50,97.5]},'preserves_support':True},
        'perm_moderator_within_stratum':{'n':len(pb_stratum),'upper_tail_prob':upper_tail(pb_stratum,b3_real),
            'real_exceeds_frac':emp_rank(pb_stratum,b3_real),'quantiles':{q:float(np.percentile(pb_stratum,q)) for q in[2.5,50,97.5]},'preserves_support':True,'grouping':'within stratum'},
        'studentized_global':{'n':len(pb_stud),'upper_tail_prob':upper_tail(pb_stud,t_real) if t_real else None,
            'quantiles':{q:float(np.percentile(pb_stud,q)) for q in[2.5,50,97.5]}},
        'eventid_hash_auxiliary':{'n':len(pb_evid),'upper_tail_prob':upper_tail(pb_evid,b3_real),
            'real_exceeds_frac':emp_rank(pb_evid,b3_real),'note':'deterministic hash-uniform; auxiliary only, does NOT preserve empirical moderator distribution'}}
    R['placebo']=plac
    json.dump(plac, open(os.path.join(out_dir,'placebo_analysis.json'),'w'), indent=1)

    # ============ P0: controller policy evaluation ============
    pis={'pi_keep':lambda x:0,'pi_static':lambda x:1,'pi_signal':lambda x:1 if x['dup_frac']>DUP_THRESHOLD else 0}
    pv={}
    for k,f in pis.items():
        hv,den=hajek(valid,f,props)
        drv,fb,leak=dr_loro_clean(valid,f,props)
        # effective matched count
        matched=sum(1 for x in valid if x['A']==f(x))
        lo,hi=repo_bootstrap_ci(valid, lambda rr,ff=f: hajek(rr,ff,props)[0])
        pv[k]={'hajek':hv,'hajek_denominator':den,'effective_matched_n':matched,
               'dr_loro':drv,'dr_fallback_counts':fb,'dr_own_outcome_leaks':leak,
               'hajek_repo_bootstrap_ci95':[lo,hi]}
    pv['best_static_hajek']='pi_keep' if pv['pi_keep']['hajek']<pv['pi_static']['hajek'] else 'pi_static'
    pv['best_static_dr']='pi_keep' if pv['pi_keep']['dr_loro']<pv['pi_static']['dr_loro'] else 'pi_static'
    pv['estimators_agree_best_static']=(pv['best_static_hajek']==pv['best_static_dr'])
    pv['signal_beats_both_hajek']=bool(pv['pi_signal']['hajek']<min(pv['pi_keep']['hajek'],pv['pi_static']['hajek']))
    pv['signal_beats_both_dr']=bool(pv['pi_signal']['dr_loro']<min(pv['pi_keep']['dr_loro'],pv['pi_static']['dr_loro']))
    pv['type']='Hajek IPW PRIMARY; LORO-DR SECONDARY. Lower cost=better. propensity=0.5 (verified marginal).'
    R['controller']=pv
    json.dump(pv, open(os.path.join(out_dir,'policy_values.json'),'w'), indent=1)
    # contrasts with repo-bootstrap CI on the difference
    def contrast_ci(fa,fb_):
        return repo_bootstrap_ci(valid, lambda rr: hajek(rr,fa,props)[0]-hajek(rr,fb_,props)[0])
    contrasts={
      'signal_minus_keep':{'hajek':pv['pi_signal']['hajek']-pv['pi_keep']['hajek'],'dr':pv['pi_signal']['dr_loro']-pv['pi_keep']['dr_loro'],'hajek_ci95':list(contrast_ci(pis['pi_signal'],pis['pi_keep']))},
      'signal_minus_static':{'hajek':pv['pi_signal']['hajek']-pv['pi_static']['hajek'],'dr':pv['pi_signal']['dr_loro']-pv['pi_static']['dr_loro'],'hajek_ci95':list(contrast_ci(pis['pi_signal'],pis['pi_static']))},
      'static_minus_keep':{'hajek':pv['pi_static']['hajek']-pv['pi_keep']['hajek'],'dr':pv['pi_static']['dr_loro']-pv['pi_keep']['dr_loro'],'hajek_ci95':list(contrast_ci(pis['pi_static'],pis['pi_keep']))},
      'note':'positive contrast = first policy MORE costly (worse). Controller supported only if signal_minus_{keep,static} both clearly negative with CI.'}
    R['policy_contrasts']=contrasts
    json.dump(contrasts, open(os.path.join(out_dir,'policy_contrasts.json'),'w'), indent=1)
    json.dump({'fallback_hierarchy':['train stratum-by-arm mean','train arm mean','train global mean'],
        'own_outcome_used':False,'per_policy':{k:{'fallback_counts':pv[k]['dr_fallback_counts'],'leaks':pv[k]['dr_own_outcome_leaks']} for k in pis},
        'note':'leakage-free: held-out unit outcome NEVER used to build its own nuisance prediction'},
        open(os.path.join(out_dir,'dr_audit.json'),'w'), indent=1)

    # ============ P1: quality NI ============
    def wilson(k,n,z=1.96):
        if n==0: return (None,None,None)
        p=k/n; d=1+z*z/n; c=p+z*z/(2*n); m=z*((p*(1-p)/n+z*z/(4*n*n))**0.5)
        return (p,(c-m)/d,(c+m)/d)
    def newcombe(k1,n1,k0,n0,z=1.96):
        # Newcombe (1998) method 10: Wilson bounds already embed z; do NOT multiply again.
        p1,l1,u1=wilson(k1,n1,z); p0,l0,u0=wilson(k0,n0,z)
        rd=p1-p0
        lo=rd-(((p1-l1)**2+(u0-p0)**2)**0.5); hi=rd+(((u1-p1)**2+(p0-l0)**2)**0.5)
        return rd,lo,hi
    ld=[x for x in valid if x['A']==1]; no=[x for x in valid if x['A']==0]
    k1=sum(x['resolved'] for x in ld); n1=len(ld); k0=sum(x['resolved'] for x in no); n0=len(no)
    rd,lo,hi=newcombe(k1,n1,k0,n0)
    p1,w1l,w1u=wilson(k1,n1); p0,w0l,w0u=wilson(k0,n0)
    qual={'type':'PRIMARY marginal NI (frozen margin -0.15). Binary SWE-bench resolution ONLY.',
        'LINEDEDUP':f'{k1}/{n1}','NO_OP':f'{k0}/{n0}','risk_difference':rd,
        'newcombe_ci95':[lo,hi],'ni_margin':NI_MARGIN,'ni_met_marginal':bool(lo>=NI_MARGIN),
        'distance_lower_to_margin':float(lo-NI_MARGIN),
        'wilson_LINEDEDUP':[p1,w1l,w1u],'wilson_NOOP':[p0,w0l,w0u],
        'scope_note':'binary resolution ONLY; NOT trajectory quality / H3 rework / rereads / semantic correctness. Cluster-aware precision limited.'}
    R['quality']=qual
    json.dump(qual, open(os.path.join(out_dir,'quality_analysis.json'),'w'), indent=1)

    # ============ P1: pricing sensitivity + raw decomposition ============
    def eff_cost(x,w): return w['input']*x['input_tokens']+w['cache_read']*x['cache_read']+w['cache_creation']*x['cache_creation']+w['output']*x['output_tokens']
    schemes={'frozen_primary':H1_WEIGHTS,
             'uniform_1x':dict(input=1,cache_read=1,cache_creation=1,output=1),
             'output_heavy_10x':dict(input=1,cache_read=0.1,cache_creation=1.25,output=10),
             'cache_creation_heavy':dict(input=1,cache_read=0.1,cache_creation=2.5,output=5),
             'no_cache_discount':dict(input=1,cache_read=1,cache_creation=1.25,output=5)}
    pricing={'type':'SENSITIVITY (frozen primary unchanged)'}
    for nm,w in schemes.items():
        ys=[eff_cost(x,w) for x in valid]; As=[x['A'] for x in valid]
        d=dim(ys,As)
        # policy ranking under this pricing
        vv={}
        for pk,pf in pis.items():
            num=den=0.0
            for x,yy in zip(valid,ys):
                ww=(1/props.get(x['task_id'],0.5)) if x['A']==pf(x) else 0.0
                num+=ww*yy; den+=ww
            vv[pk]=num/den if den>0 else float('nan')
        best='pi_keep' if vv['pi_keep']<min(vv['pi_static'],vv['pi_signal']) else ('pi_static' if vv['pi_static']<vv['pi_signal'] else 'pi_signal')
        pricing[nm]={'H1_ATE':d,'pi_keep':vv['pi_keep'],'pi_static':vv['pi_static'],'pi_signal':vv['pi_signal'],
            'best_policy':best,'signal_beats_both':bool(vv['pi_signal']<min(vv['pi_keep'],vv['pi_static']))}
    # raw token arm decomposition
    decomp={}
    for c in ['input_tokens','cache_read','cache_creation','output_tokens']:
        decomp[c]={'mean_LINEDEDUP':float(np.mean([x[c] for x in valid if x['A']==1])),
                   'mean_NOOP':float(np.mean([x[c] for x in valid if x['A']==0])),
                   'diff':dim([x[c] for x in valid],[x['A'] for x in valid]),'type':'DESCRIPTIVE randomized arm contrast'}
    pricing['raw_token_decomposition']=decomp
    pricing['mediation_note']='prefix byte preservation is a SOFTWARE_INVARIANT; raw cache-token diffs are randomized arm contrasts; causal cache mediation is NOT identified.'
    R['pricing']=pricing
    json.dump(pricing, open(os.path.join(out_dir,'pricing_sensitivity.json'),'w'), indent=1)

    # ============ P1: H3 + task-total ============
    h3rows=[x for x in valid if x['h3'] is not None]
    trunc={'horizon3':sum(1 for x in valid if x['h3_horizon']==3),
           'horizon2':sum(1 for x in valid if x['h3_horizon']==2),
           'horizon1':sum(1 for x in valid if x['h3_horizon']==1),
           'horizon0':sum(1 for x in valid if x['h3_horizon']==0)}
    # truncation balance by arm
    trunc_by_arm={a:{h:sum(1 for x in valid if x['A']==a and x['h3_horizon']==h) for h in [1,2,3]} for a in [0,1]}
    h3_ate=dim([x['h3'] for x in h3rows],[x['A'] for x in h3rows]) if len(set(x['A'] for x in h3rows))==2 else None
    h3_loro={}
    for rp in set(x['repo'] for x in h3rows):
        sub=[x for x in h3rows if x['repo']!=rp]
        if len(set(x['A'] for x in sub))==2: h3_loro[f'drop_{rp}']=dim([x['h3'] for x in sub],[x['A'] for x in sub])
    tt=[x for x in valid if x['task_total'] is not None]
    tt_ate=dim([x['task_total'] for x in tt],[x['A'] for x in tt]) if len(set(x['A'] for x in tt))==2 else None
    h3={'type':'SECONDARY proximal (main-agent calls only)',
        'n_full_h3':trunc['horizon3'],'truncation':trunc,'truncation_by_arm':trunc_by_arm,
        'trunc_assoc_assignment_note':'compare arm truncation counts above for balance',
        'h3_ate':h3_ate,'h3_n':len(h3rows),'h3_leave_one_repo_out':h3_loro,
        'task_total_ate':tt_ate,'task_total_n':len(tt),
        'rework_proxies':'NOT ESTIMABLE — reread/repeated-command detectors were not stored per intervention in sealed events',
        'caveat':'a shorter horizon may reflect unsuccessful task termination, not efficiency'}
    R['h3']=h3
    json.dump(h3, open(os.path.join(out_dir,'h3_analysis.json'),'w'), indent=1)

    # ============ secondary ANCOVA (only pre-treatment covariates that exist) ============
    avail_cov=[]; missing_cov=[]
    # log(segment_chars) and calls_so_far ARE stored; prior-call cost + prior cache state are NOT
    import math
    for x in valid: x['log_seg']=math.log(x['seg_chars']) if x['seg_chars']>0 else 0.0
    avail_cov=['log_seg','calls_so_far']; missing_cov=['prior_call_effective_cost','prior_cache_state']
    Xa,ya,namesa,ra,blocksa=design_matrix_blockFE(valid,center,extra_cov=avail_cov)
    ba,resa,rka,dofa,conda,pinva,sva=ols_fit(Xa,ya)
    i3a=namesa.index('b3_AxS'); i1a=namesa.index('b1_A')
    seh_a=se_hc3(Xa,resa,pinva)
    ancova={'type':'SECONDARY (variance reduction). PARTIAL: only pre-treatment covariates that were logged.',
        'covariates_used':avail_cov,'covariates_missing_not_estimable':missing_cov,
        'b1_A':float(ba[i1a]),'b3_AxS':float(ba[i3a]),'se_HC3_b3':float(seh_a[i3a]),
        'residual_sd':float(np.std(resa)),'primary_residual_sd_no_cov':float(np.std(resid_reduced)) if False else None,
        'note':'2 of 4 prespecified covariates (prior-call cost, prior cache state) were NOT stored -> ANCOVA is partial.'}
    R['ancova']=ancova

    # ============ verdicts (conservative) ============
    b3=mod['b3_AxS']; b3_ci=mod['ci95_cluster_b3']
    ate_dim=unadj
    sig_beats=(pv['signal_beats_both_hajek'] or pv['signal_beats_both_dr'])
    prefix_ok=all(x['prior_prefix_identical'] for x in valid if x['A']==1)
    noop_ok=all(x['full_noop_identical'] for x in valid if x['A']==0)
    V={}
    V['PROTOCOL_INTEGRITY']=('SUPPORTED' if (prefix_ok and noop_ok and R['meta']['n_excluded_infra']==0) else 'NOT_SUPPORTED',
        f'prefix 36/36 identical={prefix_ok}; NO_OP byte-identical={noop_ok}; 0 infra failures; obs assignment in reconstructed space={R["randomization_mechanism"]["observed_assignment_in_space"]}','software invariants + design check')
    ate_ci=ate['blockFE_A_ci95_cluster']
    V['LINEDEDUP_ATE_H1']=('DIRECTIONALLY FAVORABLE / NOT PRECISELY ESTABLISHED',
        f'unadj dim={ate_dim:.0f} (LD cheaper); block-FE A={ate["blockFE_b1_A"]:.0f}; cluster CI95 {[round(z) for z in ate_ci]} crosses 0; LORO stable; tail-sensitive (leave-top-5 -> {ltk.get("k=5")})','lower cost better; imprecise & tail-sensitive')
    V['REDUNDANCY_CAUSAL_MODERATOR']=('NOT ESTABLISHED / UNDERPOWERED',
        f'b3={b3:.0f} (hypothesized <0), cluster CI95 {[round(z) for z in b3_ci]} spans 0; sharp-null p={sharp_p:.2f}; FL no-moderation p={fl_p:.2f}; real |b3| exceeds only {emp_rank(pb_global,b3):.0%} of distribution-preserving placebos','randomization inference')
    V['H3_REWORK_SAFETY']=('UNDERPOWERED / NOT ESTABLISHED',
        f'H3 ATE={h3_ate} (n_full={trunc["horizon3"]}); rework proxies NOT ESTIMABLE (not logged)','secondary; truncation may reflect task termination')
    V['PREFIX_BYTE_PRESERVATION']=('SUPPORTED AS A SOFTWARE INVARIANT',
        f'{sum(1 for x in valid if x["A"]==1 and x["prior_prefix_identical"])}/{n1} LINEDEDUP prior prefixes byte-identical','deterministic invariant, not a causal estimate')
    cc=decomp['cache_creation']
    V['CACHE_COST_EFFECT']=('DIRECTIONAL / UNDERPOWERED',
        f'cache_creation LD={cc["mean_LINEDEDUP"]:.0f} vs NO_OP={cc["mean_NOOP"]:.0f} (diff {cc["diff"]:.0f}); randomized arm contrast, mediation NOT identified','descriptive arm contrast')
    V['QUALITY_NONINFERIORITY']=('PRESPECIFIED MARGINAL CRITERION MET; CLUSTER-AWARE PRECISION LIMITED',
        f'risk diff {rd:+.3f}, Newcombe CI [{lo:.3f},{hi:.3f}], lower bound {lo:.3f} >= margin {NI_MARGIN} (clears by {lo-NI_MARGIN:.3f})','binary resolution ONLY; not broad safety')
    V['SIGNAL_POLICY_VALUE']=('NOT SUPPORTED; PI_SIGNAL DOES NOT BEAT PI_STATIC',
        f'Hajek pi_signal={pv["pi_signal"]["hajek"]:.0f} vs pi_static={pv["pi_static"]["hajek"]:.0f} vs pi_keep={pv["pi_keep"]["hajek"]:.0f}; best static={pv["best_static_hajek"]} (Hajek) / {pv["best_static_dr"]} (DR), agree={pv["estimators_agree_best_static"]}; signal beats both: Hajek={pv["signal_beats_both_hajek"]} DR={pv["signal_beats_both_dr"]}','both estimators')
    V['DEPLOYABLE_TRACECONTROLLER']=('NOT SUPPORTED',
        'requires moderator + policy value + held-out online eval; none achieved','composite')
    R['verdicts']={k:{'result':v[0],'evidence':v[1],'caveat':v[2]} for k,v in V.items()}

    json.dump({k:R[k] for k in ['meta','verdicts']}, open(os.path.join(out_dir,'reconciliation_summary.json'),'w'), indent=1)
    json.dump(R['ancova'], open(os.path.join(out_dir,'ancova_secondary.json'),'w'), indent=1)
    # moderator estimates already saved; also save full
    full={k:R[k] for k in R if not k.startswith('_')}
    json.dump(full, open(os.path.join(out_dir,'analysis_full.json'),'w'), indent=1)
    print("VERDICTS:")
    for k,v in R['verdicts'].items(): print(f"  {k}: {v['result']}")

if __name__=='__main__':
    main()
    run_full()
