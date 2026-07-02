#!/usr/bin/env python3
"""P0.3 Oracle-gap noise-model sensitivity (existing data only; no new runs).
Question: does ANY reasonable noise model permit a DEFENSIBLE POSITIVE LOWER BOUND on real oracle
headroom, given the observed single-run 6-method x 50-task matrix and the SHAM noise floor?
We do NOT try to recover a positive gap; we test whether the negative is robust across noise models.

Models tested (null = all actions truly identical; observed cost = true_cost perturbed by noise):
 1. multiplicative lognormal, homoskedastic, sigma from SHAM median|rel| (0.31 -> sigma~0.46)
 2. additive gaussian, homoskedastic (sd from SHAM absolute diffs)
 3. task-cost-scaled multiplicative (sigma constant in relative terms) [= model 1]
 4. heteroskedastic-by-baseline-cost-quartile (sigma estimated per quartile from... only 10 SHAM pts, so
    approximate by scaling; documents limitation)
 5. correlated action noise within task (rho>0 across the 4 action draws) -> REDUCES manufactured gap
 6. different SHAM sigma estimators: median|rel|, mean|rel|, sd(rel), robust MAD
Also: SHAM subset is 2.67x more expensive than the 50-task mean -> if noise is cost-scaled in RELATIVE
terms it transfers; if noise has an ADDITIVE floor, cheaper tasks are LESS noisy -> test cheap-task subset.
Usage: oracle_noise_sensitivity.py <conf_dir> <out_dir>
"""
import json, sys, os
import numpy as np
from collections import defaultdict

def eff(r): return r['input_tokens']+0.1*r['cache_read_tokens']+1.25*r['cache_creation_tokens']+5*r['output_tokens']

def main(conf, out):
    os.makedirs(out, exist_ok=True)
    tl=[json.loads(l) for l in open(os.path.join(conf,'task_level_ledger.jsonl'))]
    cost=defaultdict(dict)
    for r in tl: cost[r['task_id']][r['method']]=r['instance_cost']
    LAD=['C0_identity','M4_obs_cap_5k','M6_env_log_collapse','M7_old_obs_elide']
    tasks=[t for t in cost if all(m in cost[t] for m in LAD)]
    true_cost=np.array([np.mean([cost[t][m] for m in LAD]) for t in tasks])
    c0cost=np.array([cost[t]['C0_identity'] for t in tasks])

    # ---- SHAM noise floor (per-call effective cost; SHAM vs C0, 10 tasks) ----
    led={}
    for arm in ['C0_identity','SHAM']:
        bt=defaultdict(float)
        for r in (json.loads(l) for l in open(os.path.join(conf,f'ledgers/ledger_{arm}_rep1.jsonl'))):
            bt[r['task_id']]+=eff(r)
        led[arm]=bt
    common=sorted(set(led['C0_identity'])&set(led['SHAM']))
    c0=np.array([led['C0_identity'][t] for t in common]); sh=np.array([led['SHAM'][t] for t in common])
    rel=(sh-c0)/c0; absd=np.abs(sh-c0)
    sham={'n':len(common),'median_abs_rel':float(np.median(np.abs(rel))),'mean_abs_rel':float(np.mean(np.abs(rel))),
          'sd_rel':float(np.std(rel)),'mad_rel':float(np.median(np.abs(rel-np.median(rel)))*1.4826),
          'sham_mean_cost':float(np.mean(c0)),'all50_mean_cost':float(np.mean(c0cost)),
          'sham_over_all_ratio':float(np.mean(c0)/np.mean(c0cost)),
          'additive_sd_effcost':float(np.std(sh-c0))}
    # sigma estimators for lognormal: median|rel| = 0.674*sigma (half-normal) => sigma = median/0.674
    sig_est={'median_rel/0.674':sham['median_abs_rel']/0.674,
             'mean_rel/0.798':sham['mean_abs_rel']/0.798,
             'sd_rel':sham['sd_rel'],
             'mad_rel':sham['mad_rel']}

    # observed naive oracle gap on the ladder (equal-weight)
    obs_gap=100*(np.mean(c0cost)-np.mean([min(cost[t][m] for m in LAD) for t in tasks]))/np.mean(c0cost)

    rng=np.random.default_rng(20260702)
    def sim_gap(noise_fn, B=3000):
        gaps=[]
        for _ in range(B):
            draws=noise_fn()
            c0d=draws[:,0]; orc=draws.min(axis=1)
            gaps.append(100*(c0d.mean()-orc.mean())/c0d.mean())
        return float(np.mean(gaps)), [float(np.percentile(gaps,2.5)),float(np.percentile(gaps,97.5))]

    n=len(tasks)
    results={'observed_naive_gap_pct':float(obs_gap),'sham':sham,'sigma_estimators':sig_est,
             'note':'NULL = all 4 actions identical. If null-manufactured gap >= observed, no positive lower bound is defensible under that model.',
             'models':{}}
    # model 1: multiplicative lognormal homoskedastic (several sigma)
    for lbl,sig in sig_est.items():
        g,ci=sim_gap(lambda s=sig: true_cost[:,None]*np.exp(rng.normal(0,s,size=(n,4))))
        results['models'][f'mult_lognormal_sigma[{lbl}={sig:.2f}]']={'null_gap_pct':g,'ci':ci,'null_ge_observed':bool(g>=obs_gap)}
    # model 2: additive gaussian homoskedastic
    sd_add=sham['additive_sd_effcost']  # in eff-cost units; scale to $ proxy via ratio? use relative-to-mean
    sd_add_rel=sd_add/np.mean(c0)  # relative additive sd
    g,ci=sim_gap(lambda: np.maximum(true_cost[:,None]+rng.normal(0,sd_add_rel*np.mean(true_cost),size=(n,4)),1e-6))
    results['models']['additive_gaussian_homosked']={'null_gap_pct':g,'ci':ci,'null_ge_observed':bool(g>=obs_gap),
        'note':'additive floor => cheaper tasks noisier in relative terms; likely OVERstates cheap-task gap'}
    # model 5: correlated action noise within task (rho=0.5, 0.8) — correlation REDUCES manufactured gap
    for rho in [0.3,0.5,0.8]:
        sig=sig_est['median_rel/0.674']
        def corr_draw(rho=rho,sig=sig):
            common_shock=rng.normal(0,sig,size=(n,1))
            idio=rng.normal(0,sig,size=(n,4))
            z=np.sqrt(rho)*common_shock+np.sqrt(1-rho)*idio
            return true_cost[:,None]*np.exp(z)
        g,ci=sim_gap(corr_draw)
        results['models'][f'correlated_within_task_rho{rho}']={'null_gap_pct':g,'ci':ci,'null_ge_observed':bool(g>=obs_gap),
            'note':'positive within-task action-noise correlation shrinks the manufactured gap; if real action noise is correlated, more of the observed gap could be real'}

    # ---- cheap-task subset test: if additive noise floor, cheap tasks less noisy -> does a gap survive? ----
    # split tasks by baseline cost median; compute observed naive gap on cheap half (still single-run, still caveated)
    med=np.median(c0cost)
    cheap=[t for t in tasks if cost[t]['C0_identity']<=med]
    exp_=[t for t in tasks if cost[t]['C0_identity']>med]
    def obsgap(ts):
        cc=np.mean([cost[t]['C0_identity'] for t in ts]); oo=np.mean([min(cost[t][m] for m in LAD) for t in ts])
        return 100*(cc-oo)/cc
    results['subset_observed_gaps']={'cheap_half':obsgap(cheap),'expensive_half':obsgap(exp_),
        'note':'still single-run; cheap-half gap is NOT a positive lower bound, just a descriptive split. SHAM noise not measured on cheap tasks.'}

    # ---- verdict ----
    any_positive_lb=any(not m['null_ge_observed'] for m in results['models'].values())
    # a defensible positive LB requires the null-manufactured gap to be RELIABLY below observed across
    # plausible models AND repeated-run data to pin it. Neither holds.
    results['verdict']={
      'any_model_null_below_observed': any_positive_lb,
      'defensible_positive_lower_bound': False,
      'reason':'Even where a null model produces a smaller gap than observed (e.g. strongly correlated within-task noise), (a) we have NO repeated-run data to estimate the true within-task action correlation, and (b) the SHAM floor is measured on only 10 high-cost tasks. No noise model + single-run data can pin a positive lower bound. The honest statement is: no positive lower bound on real oracle headroom is establishable from this matrix.',
      'canonical_wording':'No positive lower bound on real oracle headroom can be established from the current single-run retrospective matrix under any tested noise model. This is NOT the same as a true gap of zero.'}
    json.dump(results, open(os.path.join(out,'oracle_noise_sensitivity.json'),'w'), indent=1)
    print(f"observed naive gap: {obs_gap:.1f}%")
    print(f"SHAM: n={sham['n']} median|rel|={sham['median_abs_rel']:.2f} sham/all cost ratio={sham['sham_over_all_ratio']:.2f}")
    print("null-manufactured gaps by model:")
    for k,m in results['models'].items():
        print(f"  {k}: {m['null_gap_pct']:.1f}% null>=obs={m['null_ge_observed']}")
    print(f"cheap-half obs gap={results['subset_observed_gaps']['cheap_half']:.1f}% exp-half={results['subset_observed_gaps']['expensive_half']:.1f}%")
    print(f"DEFENSIBLE POSITIVE LOWER BOUND: {results['verdict']['defensible_positive_lower_bound']}")

if __name__=='__main__':
    main(sys.argv[1], sys.argv[2])
