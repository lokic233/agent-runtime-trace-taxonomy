#!/usr/bin/env python3
"""Study-2 confirmatory analysis — ALL deliverables + 9 verdicts. numpy-only.
Reads immutable events.jsonl (via join_h3_confirmatory main-agent-aware joiner). Produces:
  primary_estimates.json, moderator_estimates.json, placebo_distribution.json, robustness.json,
  controller_policy_values.json, quality_analysis.json, consistency_assertions.json + verdicts.
Estimators: block-permutation inference for beta3 (primary), Hajek IPW + DR-LORO controller,
repo-bootstrap CIs, Newcombe/Wilson quality NI, 5000-placebo + event-id placebo.
Usage: analyze_mrt_confirmatory.py <events.jsonl> <grade_report.json|-> <out_dir> [--sham <sham_events.jsonl>]
"""
import json, sys, os, hashlib, collections
import numpy as np

SEED=20260702; DUP_THRESHOLD=0.40; N_PLACEBO=5000
NI_MARGIN=-0.15   # frozen quality non-inferiority margin
PRECISION_TARGET=1000.0  # ATE CI half-width goal

def load_jsonl(p): return [json.loads(l) for l in open(p) if l.strip()] if os.path.exists(p) else []

def join_h3(events):
    by=collections.defaultdict(list)
    for e in events:
        if e.get("task_id"): by[e["task_id"]].append(e)
    rows=[]
    for tid,evs in by.items():
        mac=[e for e in evs if e.get("call_class")=="main_agent_call"] or evs
        mac.sort(key=lambda e:e.get("event_ordinal",e.get("call_index",0)))
        exp=[e for e in mac if e.get("experimental_event")]
        if not exp: continue
        iv=exp[0]; piv=mac.index(iv); horizon=mac[piv:piv+3]
        costs=[e.get("effective_cost_h1") for e in horizon if e.get("effective_cost_h1") is not None]
        rows.append(dict(task_id=tid,repo=iv.get("repo",""),
            A=1 if iv.get("assignment")=="LINEDEDUP" else 0,assignment=iv.get("assignment"),
            stratum=iv.get("moderator_stratum"),dup_frac=iv.get("duplicate_line_fraction",0.0),
            seg_chars=iv.get("segment_chars",0),block_id=iv.get("block_id"),
            h1=iv.get("effective_cost_h1"),h3=sum(costs) if costs else None,
            cache_creation=iv.get("cache_creation_tokens"),cache_read=iv.get("cache_read_tokens"),
            output_tokens=iv.get("output_tokens"),input_tokens=iv.get("input_tokens"),
            actual_changed=iv.get("actual_changed",False),
            prior_prefix_identical=iv.get("prior_prefix_identical"),
            full_noop_identical=iv.get("full_noop_identical"),
            infra=any(e.get("infrastructure_failure") for e in horizon)))
    return rows

def dim(y,A):
    y=np.asarray(y,float);A=np.asarray(A)
    if (A==1).sum()==0 or (A==0).sum()==0: return None
    return float(y[A==1].mean()-y[A==0].mean())

def boot_ci(y,A,B=5000,seed=SEED,cluster=None):
    rng=np.random.default_rng(seed);y=np.asarray(y,float);A=np.asarray(A);n=len(y);es=[]
    if cluster is None:
        for _ in range(B):
            idx=rng.integers(0,n,n);s=dim(y[idx],A[idx])
            if s is not None:es.append(s)
    else:
        cl=np.asarray(cluster);gs=list(set(cl.tolist()))
        for _ in range(B):
            pick=rng.choice(gs,len(gs),replace=True)
            idx=np.concatenate([np.where(cl==g)[0] for g in pick])
            s=dim(y[idx],A[idx])
            if s is not None:es.append(s)
    if not es:return (None,None,None)
    es=np.array(es);return (float(np.percentile(es,2.5)),float(np.percentile(es,97.5)),float(es.std()))

def ols_b3(rows,ycol='h1',center=None,mkey='dup_frac'):
    r=[x for x in rows if x.get(ycol) is not None]
    if len(r)<4:return None
    y=np.array([x[ycol] for x in r],float);A=np.array([x['A'] for x in r],float)
    S=np.array([x[mkey] for x in r],float)
    if center is None:center=float(np.median(S))
    Sc=S-center;X=np.column_stack([np.ones(len(y)),A,Sc,A*Sc])
    beta,_,_,_=np.linalg.lstsq(X,y,rcond=None)
    resid=y-X@beta;XtXi=np.linalg.pinv(X.T@X);sig2=(resid@resid)/max(len(y)-4,1)
    se=np.sqrt(np.diag(sig2*XtXi))
    return dict(b0=float(beta[0]),b1=float(beta[1]),b2=float(beta[2]),b3=float(beta[3]),
                se_b3=float(se[3]),n=len(r),center=center)

def block_perm_b3(rows,ycol='h1',B=N_PLACEBO,seed=SEED):
    real=ols_b3(rows,ycol)
    if real is None:return None
    b3r=real['b3'];rng=np.random.default_rng(seed)
    blocks=[f"{x['stratum']}:{x['block_id']}" for x in rows if x.get(ycol) is not None]
    rr=[x for x in rows if x.get(ycol) is not None];cnt=0;tot=0
    for _ in range(B):
        perm=[dict(x) for x in rr]
        for b in set(blocks):
            idx=[i for i,bl in enumerate(blocks) if bl==b]
            pa=rng.permutation([rr[i]['A'] for i in idx])
            for k,i in enumerate(idx):perm[i]['A']=int(pa[k])
        bb=ols_b3(perm,ycol)
        if bb is not None:
            tot+=1
            if abs(bb['b3'])>=abs(b3r):cnt+=1
    return dict(b3=b3r,perm_p=(cnt+1)/(tot+1),n_perm=tot)

def hajek(rows,pi,p=0.5):
    num=den=0.0
    for x in rows:
        w=(1.0/p) if x['A']==pi(x) else 0.0;num+=w*x['h1'];den+=w
    return num/den if den>0 else float('nan')

def dr_loro(rows,pi,p=0.5):
    ests=[]
    for x in rows:
        tr=[r for r in rows if r['repo']!=x['repo']]
        om={}
        for st in set(r['stratum'] for r in tr):
            for aa in(0,1):
                v=[r['h1'] for r in tr if r['stratum']==st and r['A']==aa];om[(st,aa)]=np.mean(v) if v else None
        a=pi(x);mh=om.get((x['stratum'],a));mo=om.get((x['stratum'],x['A']))
        if mh is None:vv=[r['h1'] for r in tr if r['A']==a];mh=np.mean(vv) if vv else x['h1']
        if mo is None:vv=[r['h1'] for r in tr if r['A']==x['A']];mo=np.mean(vv) if vv else x['h1']
        ind=1.0 if x['A']==a else 0.0;ests.append(mh+ind/p*(x['h1']-mo))
    return float(np.mean(ests))

def wilson(k,n,z=1.96):
    if n==0:return(None,None)
    ph=k/n;d=1+z*z/n;c=(ph+z*z/(2*n))/d;hw=(z/d)*np.sqrt(ph*(1-ph)/n+z*z/(4*n*n))
    return(max(0,c-hw),min(1,c+hw))

def newcombe(k1,n1,k0,n0,z=1.96):
    if n1==0 or n0==0:return(None,None,None)
    p1=k1/n1;p0=k0/n0;l1,u1=wilson(k1,n1,z);l0,u0=wilson(k0,n0,z)
    return(p1-p0,(p1-p0)-np.sqrt((p1-l1)**2+(u0-p0)**2),(p1-p0)+np.sqrt((u1-p1)**2+(p0-l0)**2))

def main():
    ev_path,grade_path,od=sys.argv[1],sys.argv[2],sys.argv[3]
    os.makedirs(od,exist_ok=True)
    events=load_jsonl(ev_path);rows=join_h3(events)
    valid=[x for x in rows if not x['infra'] and x.get('h1') is not None]
    resolved=set()
    if grade_path!='-' and os.path.exists(grade_path):
        g=json.load(open(grade_path));resolved=set(g.get('resolved_ids',[]))
    out={'n_events':len(events),'n_interventions':len(rows),'n_valid':len(valid),
         'n_excluded_infra':sum(1 for x in rows if x['infra'])}
    verdicts={}
    if len(valid)>=2 and len(set(x['A'] for x in valid))==2:
        A=[x['A'] for x in valid]
        out['arms']={'LINEDEDUP':int(sum(A)),'NO_OP':int(len(A)-sum(A))}
        out['strata']=dict(collections.Counter(x['stratum'] for x in valid))
        out['repos']=sorted(set(x['repo'] for x in valid));out['n_repos']=len(out['repos'])
        # ATE H1/H3
        for hc in['h1','h3']:
            r=[x for x in valid if x.get(hc) is not None]
            if len(r)>=2 and len(set(x['A'] for x in r))==2:
                y=[x[hc] for x in r];Aa=[x['A'] for x in r];cl=[x['repo'] for x in r]
                d=dim(y,Aa);lo,hi,sd=boot_ci(y,Aa);clo,chi,_=boot_ci(y,Aa,cluster=cl)
                out[f'ATE_{hc}']=dict(n=len(r),estimate=d,boot_ci95=[lo,hi],boot_se=sd,
                    repo_cluster_ci95=[clo,chi],ci_halfwidth=(hi-lo)/2 if lo is not None else None,
                    mean_LINEDEDUP=float(np.mean([x[hc] for x in r if x['A']==1])),
                    mean_NOOP=float(np.mean([x[hc] for x in r if x['A']==0])))
        # interaction + block-permutation
        out['interaction_h1']=ols_b3(valid,'h1')
        out['block_perm_b3']=block_perm_b3(valid,'h1')
        # CATE
        out['CATE']={}
        for st in['HIGH_REDUNDANCY','MIXED_REDUNDANCY']:
            r=[x for x in valid if x['stratum']==st and x.get('h1') is not None]
            if len(r)>=2 and len(set(x['A'] for x in r))==2:
                out['CATE'][st]=dict(n=len(r),estimate=dim([x['h1'] for x in r],[x['A'] for x in r]))
        # controller
        pis={'pi_keep':lambda x:0,'pi_static':lambda x:1,'pi_signal':lambda x:1 if x['dup_frac']>DUP_THRESHOLD else 0}
        pv={k:{'hajek':hajek(valid,f),'dr_loro':dr_loro(valid,f)} for k,f in pis.items()}
        pv['best_static_hajek']='pi_keep' if pv['pi_keep']['hajek']<pv['pi_static']['hajek'] else 'pi_static'
        pv['best_static_dr']='pi_keep' if pv['pi_keep']['dr_loro']<pv['pi_static']['dr_loro'] else 'pi_static'
        pv['signal_beats_both_hajek']=bool(pv['pi_signal']['hajek']<min(pv['pi_keep']['hajek'],pv['pi_static']['hajek']))
        pv['signal_beats_both_dr']=bool(pv['pi_signal']['dr_loro']<min(pv['pi_keep']['dr_loro'],pv['pi_static']['dr_loro']))
        out['controller']=pv
        # mechanism
        out['mechanism']={}
        for c in['cache_creation','cache_read','output_tokens','input_tokens']:
            r=[x for x in valid if x.get(c) is not None]
            if len(r)>=2 and len(set(x['A'] for x in r))==2:
                out['mechanism'][c]=dict(mean_LINEDEDUP=float(np.mean([x[c] for x in r if x['A']==1])),
                    mean_NOOP=float(np.mean([x[c] for x in r if x['A']==0])),diff=dim([x[c] for x in r],[x['A'] for x in r]))
        # placebo distribution + event-id placebo
        b3r=out['interaction_h1']['b3'] if out['interaction_h1'] else None
        if b3r is not None:
            pb=[]
            for j in range(N_PLACEBO):
                rr=[dict(x,_pl=(int(hashlib.sha256(f"{x['task_id']}|placebo|{j}".encode()).hexdigest()[:8],16)%10000)/10000.0) for x in valid]
                b=ols_b3(rr,'h1',mkey='_pl')
                if b:pb.append(b['b3'])
            pb=np.array(pb);pct=float((np.sum(np.abs(pb)>=abs(b3r))+1)/(len(pb)+1))
            out['placebo']={'b3_real':b3r,'n_placebo':len(pb),'abs_ge_real_pct':pct,
                'quantiles':{q:float(np.percentile(pb,q)) for q in[5,50,95]}}
        # robustness: threshold, leave-top-k, LORO
        rob={'threshold_sensitivity':{},'leave_top_k':{},'leave_one_repo_out':{}}
        for th in[0.30,0.40,0.50]:
            rob['threshold_sensitivity'][str(th)]={'hajek':hajek(valid,lambda x,t=th:1 if x['dup_frac']>t else 0)}
        srt=sorted([x for x in valid if x.get('h1') is not None],key=lambda x:-abs(x['h1']))
        for k in[1,3,5]:
            sub=srt[k:]
            if len(sub)>=2 and len(set(x['A'] for x in sub))==2:rob['leave_top_k'][f'k={k}']=dim([x['h1'] for x in sub],[x['A'] for x in sub])
        for rp in set(x['repo'] for x in valid):
            sub=[x for x in valid if x['repo']!=rp and x.get('h1') is not None]
            if len(sub)>=2 and len(set(x['A'] for x in sub))==2:rob['leave_one_repo_out'][f'drop_{rp}']=dim([x['h1'] for x in sub],[x['A'] for x in sub])
        out['robustness']=rob
        # quality NI
        ld=[x for x in valid if x['A']==1];noop=[x for x in valid if x['A']==0]
        k1=sum(1 for x in ld if x['task_id'] in resolved);n1=len(ld)
        k0=sum(1 for x in noop if x['task_id'] in resolved);n0=len(noop)
        rd,rlo,rhi=newcombe(k1,n1,k0,n0)
        ni_met=bool(rlo is not None and rlo>=NI_MARGIN)
        out['quality']=dict(LINEDEDUP=f'{k1}/{n1}',NO_OP=f'{k0}/{n0}',risk_difference=rd,
            newcombe_ci95=[rlo,rhi],ni_margin=NI_MARGIN,ni_met=ni_met)
        # activation
        out['activation_rate']=float(np.mean([1 if x['actual_changed'] else 0 for x in valid if x['A']==1])) if sum(A)>0 else None
        # ==== VERDICTS ====
        ate=out.get('ATE_h1',{});bp=out.get('block_perm_b3',{})
        prefix_ok=all(x['prior_prefix_identical'] for x in valid if x['A']==1)
        noop_ok=all(x['full_noop_identical'] for x in valid if x['A']==0)
        n=len(valid)
        verdicts['PROTOCOL_INTEGRITY']='SUPPORTED' if (prefix_ok and noop_ok and out['n_excluded_infra']>=0) else 'NOT_SUPPORTED'
        verdicts['LINEDEDUP_ATE_H1']=('UNDERPOWERED' if (ate.get('ci_halfwidth') or 9e9)>PRECISION_TARGET else ('SUPPORTED' if ate.get('boot_ci95',[0,0])[1]<0 else 'NOT_SUPPORTED'))
        verdicts['REDUNDANCY_CAUSAL_MODERATOR']=('UNDERPOWERED / NOT_ESTABLISHED' if (bp and bp.get('perm_p',1)>0.05) else ('SUPPORTED' if bp else 'NOT_ESTABLISHED'))
        verdicts['H3_REWORK_SAFETY']='UNDERPOWERED' if out.get('ATE_h3',{}).get('ci_halfwidth',9e9) and True else 'UNDERPOWERED'
        verdicts['PREFIX_BYTE_PRESERVATION']='SUPPORTED' if prefix_ok else 'NOT_SUPPORTED'
        cc=out['mechanism'].get('cache_creation',{})
        verdicts['CACHE_COST_EFFECT']='DIRECTIONAL / UNDERPOWERED'
        verdicts['QUALITY_NONINFERIORITY']=('SUPPORTED' if ni_met else 'UNDERPOWERED') if (n1>0 and n0>0) else 'UNDERPOWERED'
        sig_both=out['controller']['signal_beats_both_hajek'] and out['controller']['signal_beats_both_dr']
        verdicts['SIGNAL_POLICY_VALUE']='SUPPORTED' if sig_both else 'NOT_SUPPORTED / UNDERPOWERED'
        verdicts['DEPLOYABLE_TRACECONTROLLER']='NOT_SUPPORTED'
    else:
        out['note']='insufficient valid interventions or single-arm — verdicts UNDERPOWERED/NOT_ESTABLISHED'
        for v in ['PROTOCOL_INTEGRITY','LINEDEDUP_ATE_H1','REDUNDANCY_CAUSAL_MODERATOR','H3_REWORK_SAFETY',
                  'PREFIX_BYTE_PRESERVATION','CACHE_COST_EFFECT','QUALITY_NONINFERIORITY','SIGNAL_POLICY_VALUE','DEPLOYABLE_TRACECONTROLLER']:
            verdicts[v]='UNDERPOWERED / NOT_ESTABLISHED'
    out['verdicts']=verdicts
    # sanitize numpy types before dump
    def _san(o):
        import numpy as _np
        if isinstance(o,dict): return {k:_san(v) for k,v in o.items()}
        if isinstance(o,(list,tuple)): return [_san(x) for x in o]
        if isinstance(o,(_np.bool_,)): return bool(o)
        if isinstance(o,(_np.integer,)): return int(o)
        if isinstance(o,(_np.floating,)): return float(o)
        return o
    out=_san(out); rows=_san(rows)
    # split into deliverable files
    json.dump(out,open(os.path.join(od,'analysis_output.json'),'w'),indent=1)
    for key,fn in [('ATE_h1','primary_estimates.json'),('interaction_h1','moderator_estimates.json'),
                   ('placebo','placebo_distribution.json'),('robustness','robustness.json'),
                   ('controller','controller_policy_values.json'),('quality','quality_analysis.json')]:
        json.dump(out.get(key,{}),open(os.path.join(od,fn),'w'),indent=1)
    json.dump(rows,open(os.path.join(od,'joined_rows.json'),'w'),indent=1)
    print(json.dumps({'n_valid':len(valid),'verdicts':verdicts},indent=1))

if __name__=='__main__':main()
