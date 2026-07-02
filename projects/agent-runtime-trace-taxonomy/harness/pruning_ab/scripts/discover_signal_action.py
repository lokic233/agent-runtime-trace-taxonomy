#!/usr/bin/env python3
"""Signal-Action Alignment discovery on sealed Study-2 (N=70). Analysis-only.
Learning target: B(X)=E[Y(NO_OP)-Y(LINEDEDUP)|X]  (conditional advantage of LINEDEDUP; B>0 => LINEDEDUP better).
Y=effective_cost_h1 (lower better). Known propensity p=0.5.

Pipeline:
 1. LORO cross-fit DR pseudo-outcomes B_tilde (out-of-fold mu0/mu1 via low-capacity ridge).
 2. winsorization sensitivity (raw / 1-99 / 5-95).
 3. per-family exploratory advantage models -> OOF B_hat.
 4. advantage calibration (coarse bins), ranking (rank-corr / top-k gain), policy improvement.
 5. EXCEPTION policies (default LINEDEDUP, override NO_OP when predicted harm high) vs pi_static.
 6. coverage-gain curve. 7. stability across repo folds.

All model outputs are OUT-OF-FOLD. High-capacity models NOT used. Everything EXPLORATORY at N=70.
Usage: discover_signal_action.py <conf_dir> <out_dir>
"""
import json, sys, os, math, collections
import numpy as np

P=0.5
def load_jsonl(p): return [json.loads(l) for l in open(p) if l.strip()]

def ridge_fit(X,y,lam=10.0):
    Xb=np.column_stack([np.ones(len(y)),X])
    A=Xb.T@Xb + lam*np.eye(Xb.shape[1]); A[0,0]-=lam  # don't penalize intercept
    beta=np.linalg.solve(A, Xb.T@y)
    return beta
def ridge_pred(beta,X):
    Xb=np.column_stack([np.ones(len(X)),X]); return Xb@beta

def standardize(train, test):
    mu=train.mean(0); sd=train.std(0); sd[sd==0]=1.0
    return (train-mu)/sd, (test-mu)/sd

def dr_pseudo(rows, feat_cols, y_key='h1', lam=10.0):
    """LORO cross-fit. mu0,mu1 fit on training repos (low-capacity ridge on feat_cols).
    Training-only fallback (never uses own outcome). Returns rows with mu0,mu1,B_tilde,fold,fallback."""
    repos=sorted(set(r['repo'] for r in rows))
    out=[]
    audit=collections.Counter()
    for held in repos:
        tr=[r for r in rows if r['repo']!=held]
        te=[r for r in rows if r['repo']==held]
        tr0=[r for r in tr if r['A']==0]; tr1=[r for r in tr if r['A']==1]
        Xtr=np.array([[r[c] for c in feat_cols] for r in tr],float)
        # fit per arm
        def fit_arm(sub):
            if len(sub)>=max(4,len(feat_cols)+2):
                Xs=np.array([[r[c] for c in feat_cols] for r in sub],float)
                ys=np.array([r[y_key] for r in sub],float)
                Xs_std,_=standardize(Xs,Xs)
                mu=Xs.mean(0); sd=Xs.std(0); sd[sd==0]=1
                beta=ridge_fit((Xs-mu)/sd, ys, lam)
                return ('ridge',beta,mu,sd, np.mean(ys))
            elif sub:
                return ('mean',None,None,None, np.mean([r[y_key] for r in sub]))
            else:
                return ('global',None,None,None, np.mean([r[y_key] for r in tr]))
        m0=fit_arm(tr0); m1=fit_arm(tr1)
        def pred(m,r):
            kind,beta,mu,sd,gm=m
            if kind=='ridge':
                x=(np.array([[r[c] for c in feat_cols]],float)-mu)/sd
                return float(ridge_pred(beta,x)[0]), kind
            return gm, kind
        for r in te:
            mu0,k0=pred(m0,r); mu1,k1=pred(m1,r)
            audit[f'mu0_{k0}']+=1; audit[f'mu1_{k1}']+=1
            A=r['A']; Y=r[y_key]
            # B = mu0 - mu1 + (1-A)/(1-p)*(Y-mu0) - A/p*(Y-mu1)
            Bt = (mu0-mu1) + (1-A)/(1-P)*(Y-mu0) - A/P*(Y-mu1)
            rr=dict(r); rr['mu0']=mu0; rr['mu1']=mu1; rr['B_tilde']=Bt; rr['fold']=held
            rr['fallback']=f'mu0:{k0},mu1:{k1}'; rr['own_outcome_used']=False
            out.append(rr)
    return out, dict(audit)

def winsorize(vals, lo, hi):
    a=np.array(vals,float); ql,qh=np.percentile(a,[lo,hi]); return np.clip(a,ql,qh)

def hajek_value(rows, pi):
    num=den=0.0
    for x in rows:
        w=(1.0/P) if x['A']==pi(x) else 0.0
        num+=w*x['h1']; den+=w
    return num/den if den>0 else float('nan')

def main(conf_dir,out_dir):
    os.makedirs(out_dir,exist_ok=True)
    feats=load_jsonl(os.path.join(conf_dir,'pre_treatment_features.jsonl'))
    events=load_jsonl(os.path.join(conf_dir,'events.jsonl'))
    cost={e['task_id']:e['effective_cost_h1'] for e in events if e.get('experimental_event')}
    for f in feats: f['h1']=cost[f['task_id']]
    N=len(feats)

    # feature families (drop zero-variance)
    families={
      'F1_removal':['duplicate_line_fraction','removable_fraction_est','longest_dup_span','distinct_dup_spans','dup_position_mean'],
      'F2_liveness':['seg_contains_error','seg_looks_like_test_output','seg_entity_live_fraction','entity_recurrence_prevK','seg_n_funcs'],
      'F3_recoverability':['seg_looks_like_file_read','seg_reproducible_from_repo','seg_looks_like_test_output'],
      'F4_cache':['materialized_prefix_est','calls_so_far','segment_pos_in_context'],
      'F5_trajectory':['patch_exists_prior','tests_run_prior','latest_test_failed','error_loop_count','phase_diagnosis'],
      'INT_live_recov':['seg_entity_live_fraction','seg_reproducible_from_repo','error_loop_count'],
      'INT_removal_cache':['removable_fraction_est','materialized_prefix_est','calls_so_far'],
    }
    # drop constant features
    def nonconst(cols):
        return [c for c in cols if len(set(f[c] for f in feats))>1]
    families={k:nonconst(v) for k,v in families.items()}

    # ===== 1. DR pseudo-outcomes (full feature union, ridge) + winsor sensitivity =====
    union=sorted(set(c for v in families.values() for c in v))
    oof, audit = dr_pseudo(feats, union)
    Bt_raw=[r['B_tilde'] for r in oof]
    result={'meta':{'n':N,'estimand':'B(X)=E[Y(NO_OP)-Y(LINEDEDUP)|X], B>0 => LINEDEDUP better, Y=eff_cost_h1',
                    'exploratory':True,'propensity':P,'crossfit':'leave-one-repo-out','model':'ridge lam=10 (low-capacity)'},
            'dr_audit':audit, 'own_outcome_used':any(r['own_outcome_used'] for r in oof)}
    # mean B_tilde (=DR ATE of NO_OP-LINEDEDUP => should be +ATE since ATE(LD-NO)=-995 => B~+995)
    result['mean_B_tilde']={'raw':float(np.mean(Bt_raw)),
        'winsor_1_99':float(np.mean(winsorize(Bt_raw,1,99))),
        'winsor_5_95':float(np.mean(winsorize(Bt_raw,5,95)))}
    # save oof
    with open(os.path.join(conf_dir,'oof_counterfactual_advantage.jsonl'),'w') as fo:
        for r in oof:
            fo.write(json.dumps({k:r[k] for k in ['task_id','repo','A','h1','mu0','mu1','B_tilde','fold','fallback','own_outcome_used']})+'\n')

    # ===== 3-4. per-family advantage model -> OOF B_hat, then alignment =====
    def family_oof_bhat(cols):
        """LORO: fit ridge of B_tilde on family features (train), predict OOF B_hat."""
        repos=sorted(set(r['repo'] for r in oof))
        preds={}
        for held in repos:
            tr=[r for r in oof if r['repo']!=held]; te=[r for r in oof if r['repo']==held]
            if len(tr)<len(cols)+2: 
                for r in te: preds[r['task_id']]=np.mean([t['B_tilde'] for t in tr])
                continue
            Xtr=np.array([[r[c] for c in cols] for r in tr],float); ytr=np.array([r['B_tilde'] for r in tr],float)
            mu=Xtr.mean(0); sd=Xtr.std(0); sd[sd==0]=1
            beta=ridge_fit((Xtr-mu)/sd,ytr,10.0)
            for r in te:
                x=(np.array([[r[c] for c in cols]],float)-mu)/sd
                preds[r['task_id']]=float(ridge_pred(beta,x)[0])
        return preds

    fam_results={}
    for fam,cols in families.items():
        if not cols: continue
        bhat=family_oof_bhat(cols)
        # rank correlation between predicted B_hat and pseudo-outcome B_tilde (Spearman via ranks)
        xs=np.array([bhat[r['task_id']] for r in oof]); ys=np.array([r['B_tilde'] for r in oof])
        def spearman(a,b):
            ra=np.argsort(np.argsort(a)); rb=np.argsort(np.argsort(b))
            return float(np.corrcoef(ra,rb)[0,1])
        rho=spearman(xs,ys)
        # EXCEPTION policy: override to NO_OP when predicted B_hat < 0 (LINEDEDUP predicted harmful)
        # evaluate V(pi_exc) vs pi_static via Hajek on the SAME oof rows
        def pi_exc(r): return 0 if bhat[r['task_id']]<0 else 1   # 0=NO_OP override, 1=LINEDEDUP default
        v_exc=hajek_value(oof, pi_exc); v_static=hajek_value(oof, lambda r:1); v_keep=hajek_value(oof, lambda r:0)
        coverage=np.mean([1 for r in oof if pi_exc(r)==0])/1.0 if oof else 0
        coverage=sum(1 for r in oof if bhat[r['task_id']]<0)/len(oof)
        # stability across repo folds: sign of (V_exc - V_static) computed leaving each repo out
        fold_diffs=[]
        for held in sorted(set(r['repo'] for r in oof)):
            sub=[r for r in oof if r['repo']!=held]
            fd=hajek_value(sub,pi_exc)-hajek_value(sub,lambda r:1)
            fold_diffs.append(fd)
        fam_results[fam]={'features':cols,'spearman_bhat_btilde':rho,
            'V_exception':v_exc,'V_static':v_static,'V_keep':v_keep,
            'V_exc_minus_static':v_exc-v_static,'coverage_override_frac':coverage,
            'beats_static':bool(v_exc<v_static),
            'fold_diff_median':float(np.median(fold_diffs)),'fold_diff_worst':float(np.max(fold_diffs)),
            'folds_improving':int(sum(1 for d in fold_diffs if d<0)),'n_folds':len(fold_diffs),
            'exploratory':True}
    result['family_alignment']=fam_results

    # ===== advantage calibration on the UNION model B_hat =====
    bhat_union=family_oof_bhat(union)
    order=sorted(oof,key=lambda r:bhat_union[r['task_id']])
    # 3 coarse bins (N=70 -> ~23 each)
    nb=3; bins=np.array_split(order,nb)
    cal=[]
    for bi,b in enumerate(bins):
        # DR benefit within bin = mean B_tilde
        mb=float(np.mean([r['B_tilde'] for r in b]))
        cal.append({'bin':bi,'n':len(b),'mean_pred_Bhat':float(np.mean([bhat_union[r['task_id']] for r in b])),
                    'mean_DR_benefit_Btilde':mb,'n_LD':sum(r['A'] for r in b),'n_NO':sum(1-r['A'] for r in b),
                    'repos':sorted(set(r['repo'] for r in b))})
    # monotonic?
    monotonic=all(cal[i]['mean_DR_benefit_Btilde']<=cal[i+1]['mean_DR_benefit_Btilde'] for i in range(len(cal)-1))
    result['calibration']={'bins':cal,'monotonic_increasing':monotonic,'note':'exploratory; 3 coarse bins at N=70'}

    # ===== coverage-gain curve for union exception policy =====
    thresholds=sorted(set(round(bhat_union[r['task_id']],1) for r in oof))
    cg=[]
    for tau in [-3000,-2000,-1000,-500,0,500]:
        def pol(r,t=tau): return 0 if bhat_union[r['task_id']]<t else 1
        cov=sum(1 for r in oof if bhat_union[r['task_id']]<tau)/len(oof)
        v=hajek_value(oof,pol); vs=hajek_value(oof,lambda r:1)
        cg.append({'tau':tau,'coverage_override_frac':cov,'V':v,'V_minus_static':v-vs})
    result['coverage_gain_curve']=cg

    json.dump(result, open(os.path.join(out_dir,'signal_action_alignment.json'),'w'), indent=1)
    json.dump({'families':families,'union':union}, open(os.path.join(out_dir,'feature_families.json'),'w'), indent=1)
    print("mean B_tilde (raw/w199/w595):", {k:round(v) for k,v in result['mean_B_tilde'].items()})
    print("\nfamily alignment (V_exc - V_static; NEGATIVE=beats always-LINEDEDUP):")
    for fam,r in fam_results.items():
        print(f"  {fam:18} rho={r['spearman_bhat_btilde']:+.2f} V_exc-static={r['V_exc_minus_static']:+.0f} cover={r['coverage_override_frac']:.0%} beats={r['beats_static']} folds_improving={r['folds_improving']}/{r['n_folds']}")
    print(f"\ncalibration monotonic: {monotonic}")
    for c in cal: print(f"  bin{c['bin']} n={c['n']} pred_Bhat={c['mean_pred_Bhat']:+.0f} DR_benefit={c['mean_DR_benefit_Btilde']:+.0f} (LD={c['n_LD']}/NO={c['n_NO']})")

if __name__=='__main__':
    main(sys.argv[1], sys.argv[2])
