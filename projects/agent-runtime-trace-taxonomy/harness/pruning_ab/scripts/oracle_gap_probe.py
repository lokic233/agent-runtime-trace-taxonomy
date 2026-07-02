#!/usr/bin/env python3
"""Preliminary oracle-gap / parity existence diagnostic on EXISTING paid data (no new runs).
Matrix: 6 methods (mapped to A0..A3 dose ladder) x 50 tasks, with per-task instance_cost
(provider $, cache-aware) + resolution. This is a LOWER-BOUND EXISTENCE PROBE, not the
confirmatory task-total-effective-cost study (that formula needs cache splits available for
only 2 arms x 10 tasks -> too thin). Caveated accordingly.

Tolerance-conditioned feasibility: F_i(eps)={a: Q(A0)-Q(a)<=eps}. Q=resolution (binary).
best feasible a* = argmin cost over F_i. Oracle gap = best_static - oracle (lower cost better).
Naive AND bias-corrected (split-sample + repo-level) oracle. Aggregate (cost-weighted) AND
equal-weighted task-level. Repo clustering respected. eps in {0,0.02,0.05,0.10} frozen.

Usage: oracle_gap_probe.py <conf_dir> <out_dir>
"""
import json, sys, os, math
import numpy as np
from collections import defaultdict

# frozen action->method map (dose-ordered), restricted to methods with BOTH cost + resolution.
# SHAM excluded (control). DEDUP2 has resolution but no cost ledger, so A1 uses M4 (obs_cap 5k,
# mildest content-stable transform with a cost ledger); documented as an A1 proxy.
ACTION_METHODS = {
  'A0_KEEP':'C0_identity',
  'A1_LINEDEDUP':'M4_obs_cap_5k',           # mildest content-stable transform w/ cost ledger (A1 proxy)
  'A2_MODERATE':'M6_env_log_collapse',      # content-stable moderate
  'A3_AGGRESSIVE':'M7_old_obs_elide',       # aggressive elide
}
# cost matrix available for these 6 methods (task_level_ledger); use the 4 mapped + report all
COST_METHODS = ['C0_identity','HYBRID1_m7_agg2','AGG3_recency_obs_4','M4_obs_cap_5k','M6_env_log_collapse','M7_old_obs_elide']
TOL=[0.0,0.02,0.05,0.10]

def repo_of(tid): return tid.split('__')[0]

def main(conf, out):
    os.makedirs(out,exist_ok=True)
    outc=json.load(open(os.path.join(conf,'per_task_outcomes.json')))
    methods=outc['methods']; tasks=outc['golden_50']
    # cost: instance_cost per (task,method) from task_level_ledger
    tl=[json.loads(l) for l in open(os.path.join(conf,'task_level_ledger.jsonl'))]
    cost={}; toks={}; calls={}
    for r in tl:
        cost[(r['task_id'],r['method'])]=r['instance_cost']
        toks[(r['task_id'],r['method'])]=r['tokens_sent']+5*r.get('tokens_received',0)  # crude effective-ish proxy
        calls[(r['task_id'],r['method'])]=r['api_calls']
    def resolved(t,m):
        pt=methods.get(m,{}).get('per_task',{}).get(t)
        return (1 if pt.get('resolved') else 0) if pt else None
    # restrict to tasks present in cost matrix for all COST_METHODS
    usable=[t for t in tasks if all((t,m) in cost for m in COST_METHODS) and all(resolved(t,m) is not None for m in COST_METHODS)]
    R={'meta':{'n_tasks_total':len(tasks),'n_usable':len(usable),
        'cost_metric':'instance_cost (provider $, cache-aware) — PROXY for task-total effective cost',
        'caveat':'exact cache-aware effective cost needs cache splits available only for 2 arms x 10 tasks; this probe uses provider $ (corr ~0.67-0.74 with the custom formula) as a LOWER-BOUND existence signal, NOT confirmation',
        'actions':ACTION_METHODS,'cost_methods':COST_METHODS,'tolerances':TOL,
        'repos':sorted(set(repo_of(t) for t in usable))}}
    # ---- ladder-only analysis (A0..A3) ----
    LAD=list(ACTION_METHODS.values())
    def q(t,m): return resolved(t,m)
    def c(t,m): return cost[(t,m)]
    # per-tolerance oracle & static
    def analyze(method_set, label):
        res={}
        for eps in TOL:
            # feasible per task
            best_static=None; static_vals={}
            for m in method_set:
                # static policy m: feasible on task iff Q(A0)-Q(m)<=eps; if infeasible, policy still incurs cost but is a quality violation
                # For static-policy comparison we require the policy to be feasible on ALL tasks it is applied to.
                # Standard approach: static value = mean cost if we ALWAYS use m; feasibility tracked separately.
                vals=[c(t,m) for t in usable]; static_vals[m]=float(np.mean(vals))
            # oracle: per task pick min-cost action among FEASIBLE actions
            oracle_costs=[]; oracle_choice=defaultdict(int); infeasible_tasks=0
            for t in usable:
                q0=q(t,'C0_identity')
                feas=[m for m in method_set if (q0 - q(t,m))<=eps]
                if not feas:  # nothing feasible -> must KEEP (A0), even if A0 itself 'infeasible' vs itself it's 0
                    feas=['C0_identity']; infeasible_tasks+=1
                bm=min(feas,key=lambda m:c(t,m)); oracle_costs.append(c(t,bm)); oracle_choice[bm]+=1
            oracle_val=float(np.mean(oracle_costs))
            # best static = min mean cost among statics that are feasible on ALL tasks
            feas_static={}
            for m in method_set:
                allf=all((q(t,'C0_identity')-q(t,m))<=eps for t in usable)
                if allf: feas_static[m]=static_vals[m]
            if not feas_static: feas_static={'C0_identity':static_vals['C0_identity']}
            bs=min(feas_static,key=lambda m:feas_static[m]); bs_val=feas_static[bs]
            gap=bs_val-oracle_val
            res[str(eps)]={'best_static':bs,'best_static_val':bs_val,'oracle_val':oracle_val,
                'oracle_gap_abs':gap,'oracle_gap_pct':100*gap/bs_val if bs_val else 0,
                'oracle_choice_distribution':dict(oracle_choice),
                'n_distinct_oracle_actions':len(oracle_choice),
                'feasible_static_actions':list(feas_static.keys()),'infeasible_tasks':infeasible_tasks}
        return res
    R['ladder_oracle_naive']=analyze(LAD,'A0-A3 ladder')
    R['all6_oracle_naive']=analyze(COST_METHODS,'all 6 methods')

    # ---- bias correction: split-sample (repeated random 50/50 task splits; select action set on split A, evaluate on split B) ----
    def bias_corrected(method_set, eps, B=2000, seed=20260702):
        rng=np.random.default_rng(seed); gaps=[]
        for _ in range(B):
            perm=rng.permutation(usable); half=len(perm)//2
            selset=perm[:half]; evalset=perm[half:]
            # choose oracle action per task on evalset using its OWN feasibility+cost (oracle is per-task, so split matters for the STATIC winner-curse)
            # winner's curse mainly inflates 'best static' selection; select best static on selset, evaluate on evalset
            def static_mean(m,ts): return np.mean([c(t,m) for t in ts])
            feas_static=[m for m in method_set if all((q(t,'C0_identity')-q(t,m))<=eps for t in selset)] or ['C0_identity']
            bs=min(feas_static,key=lambda m:static_mean(m,selset))
            bs_val_eval=static_mean(bs,evalset)
            # oracle on evalset (per-task, honest)
            oc=[]
            for t in evalset:
                q0=q(t,'C0_identity'); feas=[m for m in method_set if (q0-q(t,m))<=eps] or ['C0_identity']
                oc.append(min(c(t,m) for m in feas))
            gaps.append(bs_val_eval-np.mean(oc))
        return float(np.mean(gaps)), [float(np.percentile(gaps,2.5)),float(np.percentile(gaps,97.5))]
    R['ladder_oracle_bias_corrected']={}
    for eps in TOL:
        g,ci=bias_corrected(LAD,eps)
        bsv=R['ladder_oracle_naive'][str(eps)]['best_static_val']
        R['ladder_oracle_bias_corrected'][str(eps)]={'gap_abs_splitsample':g,'gap_pct':100*g/bsv if bsv else 0,'ci95':ci}

    # ---- equal-weight vs cost-weight already equal-weight (mean over tasks). Add cost-weighted (sum) ----
    R['weighting_note']='primary = equal-weight task-level mean (above). Cost-weighted below.'
    def cost_weighted_gap(method_set,eps):
        # total cost of best static (feasible-all) vs total oracle cost
        na=R['ladder_oracle_naive'][str(eps)] if method_set==LAD else R['all6_oracle_naive'][str(eps)]
        bs=na['best_static']
        tot_static=sum(c(t,bs) for t in usable)
        tot_oracle=0
        for t in usable:
            q0=q(t,'C0_identity'); feas=[m for m in method_set if (q0-q(t,m))<=eps] or ['C0_identity']
            tot_oracle+=min(c(t,m) for m in feas)
        return {'total_static':tot_static,'total_oracle':tot_oracle,'gap_abs':tot_static-tot_oracle,
                'gap_pct':100*(tot_static-tot_oracle)/tot_static if tot_static else 0}
    R['ladder_cost_weighted']={str(eps):cost_weighted_gap(LAD,eps) for eps in TOL}

    # ---- outlier sensitivity: drop top-k cost tasks ----
    R['outlier_sensitivity']={}
    base_order=sorted(usable,key=lambda t:-c(t,'C0_identity'))
    for k in [1,3,5]:
        sub=base_order[k:]
        # recompute naive gap at eps=0.05 on sub
        eps=0.05
        def sm(m): return np.mean([c(t,m) for t in sub])
        feas_static=[m for m in LAD if all((q(t,'C0_identity')-q(t,m))<=eps for t in sub)] or ['C0_identity']
        bs=min(feas_static,key=sm)
        oc=[min(c(t,m) for m in ([mm for mm in LAD if (q(t,'C0_identity')-q(t,mm))<=eps] or ['C0_identity'])) for t in sub]
        R['outlier_sensitivity'][f'drop_top{k}_eps0.05']={'oracle_gap_abs':sm(bs)-np.mean(oc),'oracle_gap_pct':100*(sm(bs)-np.mean(oc))/sm(bs)}

    json.dump(R, open(os.path.join(out,'oracle_gap.json'),'w'), indent=1)
    # print summary
    print("=== ORACLE GAP (ladder A0-A3, provider-$ proxy) ===")
    print(f"usable tasks: {len(usable)} | repos: {len(R['meta']['repos'])}")
    for eps in TOL:
        n=R['ladder_oracle_naive'][str(eps)]; b=R['ladder_oracle_bias_corrected'][str(eps)]
        print(f"  eps={eps}: best_static={n['best_static']} naive_gap={n['oracle_gap_pct']:.1f}% "
              f"bias_corr_gap={b['gap_pct']:+.1f}% (CI [{b['ci95'][0]:.4f},{b['ci95'][1]:.4f}]) "
              f"oracle_actions={n['n_distinct_oracle_actions']} {dict(n['oracle_choice_distribution'])}")
    print("outlier (drop-top-k, eps0.05):", {k:round(v['oracle_gap_pct'],1) for k,v in R['outlier_sensitivity'].items()})

if __name__=='__main__':
    main(sys.argv[1],sys.argv[2])
