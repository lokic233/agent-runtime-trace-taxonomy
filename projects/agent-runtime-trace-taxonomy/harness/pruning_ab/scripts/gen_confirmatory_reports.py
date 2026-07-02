#!/usr/bin/env python3
"""Generate all Study-2 markdown reports from the confirmatory analysis JSON (auto-derived numbers).
Usage: gen_confirmatory_reports.py <analysis_dir> <reports_dir>
Produces MRT_CONFIRMATORY_{PRIMARY_RESULTS,ROBUSTNESS,CONTROLLER_VALUE,DATA_AUDIT,FINAL}.md
"""
import json, sys, os

def g(d,*ks,default=None):
    for k in ks:
        if not isinstance(d,dict): return default
        d=d.get(k,default)
    return d

def main():
    ad,rd=sys.argv[1],sys.argv[2]
    o=json.load(open(os.path.join(ad,'analysis_output.json')))
    v=o.get('verdicts',{})
    n=o.get('n_valid',0)
    ate=o.get('ATE_h1',{}); ate3=o.get('ATE_h3',{}); im=o.get('interaction_h1') or {}
    bp=o.get('block_perm_b3') or {}; ctl=o.get('controller',{}); q=o.get('quality',{})
    pl=o.get('placebo',{}); rob=o.get('robustness',{}); mech=o.get('mechanism',{})

    # DATA AUDIT
    with open(os.path.join(rd,'MRT_CONFIRMATORY_DATA_AUDIT.md'),'w') as f:
        f.write(f"""# MRT Confirmatory (Study 2) — Data Audit

Auto-generated from `results/pruning_ab/mrt_confirmatory/analysis_output.json`.
Frozen confirmatory shim, seed 20260702, opus-4.7 temp=0, thinking OFF.

| quantity | value |
|---|---|
| total logged events | {o.get('n_events')} |
| randomized interventions | {o.get('n_interventions')} |
| valid (excl. infra failures) | {n} |
| excluded (infra failure) | {o.get('n_excluded_infra')} |
| arms | {o.get('arms')} |
| strata | {o.get('strata')} |
| repos | {o.get('n_repos')} ({', '.join(o.get('repos',[]))}) |
| activation rate (LINEDEDUP changed) | {o.get('activation_rate')} |

Stopping rule: precision target (ATE CI half-width<=1000) OR pool exhaustion; never on p-value/trend.
""")

    # PRIMARY RESULTS
    with open(os.path.join(rd,'MRT_CONFIRMATORY_PRIMARY_RESULTS.md'),'w') as f:
        f.write(f"""# MRT Confirmatory (Study 2) — Primary Results

**N = {n} randomized interventions.** All numbers auto-derived from immutable artifacts.
Independent of Study 1 (new tasks, seed 20260702). Estimates are effect-size + CI.

## Primary estimand — ITT ATE(H1), LINEDEDUP − NO_OP (lower=better)
| quantity | value |
|---|---|
| ATE(H1) | {round(ate.get('estimate'),1) if ate.get('estimate') is not None else 'n/a'} |
| bootstrap 95% CI | {[round(x,0) for x in ate.get('boot_ci95',[])] if ate.get('boot_ci95') else 'n/a'} |
| repo-clustered 95% CI | {[round(x,0) for x in ate.get('repo_cluster_ci95',[])] if ate.get('repo_cluster_ci95') else 'n/a'} |
| CI half-width | {round(ate.get('ci_halfwidth'),0) if ate.get('ci_halfwidth') is not None else 'n/a'} |
| mean LINEDEDUP / NO_OP | {round(ate.get('mean_LINEDEDUP',0),0)} / {round(ate.get('mean_NOOP',0),0)} |

## ATE(H3)
estimate {round(ate3.get('estimate'),1) if ate3.get('estimate') is not None else 'n/a'}, 95% CI {[round(x,0) for x in ate3.get('boot_ci95',[])] if ate3.get('boot_ci95') else 'n/a'}.

## Primary moderator — interaction beta3 (block-permutation inference)
- descriptive b3 = {round(im.get('b3'),1) if im.get('b3') is not None else 'n/a'} (robust SE {round(im.get('se_b3'),1) if im.get('se_b3') is not None else 'n/a'}, center dup_frac {round(im.get('center'),3) if im.get('center') is not None else 'n/a'})
- **block-respecting randomization test p = {round(bp.get('perm_p'),3) if bp.get('perm_p') is not None else 'n/a'}** ({bp.get('n_perm','?')} permutations)

## CATE by stratum
{json.dumps(o.get('CATE',{}),indent=1)}
""")

    # ROBUSTNESS
    with open(os.path.join(rd,'MRT_CONFIRMATORY_ROBUSTNESS.md'),'w') as f:
        f.write(f"""# MRT Confirmatory (Study 2) — Robustness & Falsification

## Placebo distribution (5000 deterministic placebos)
- real b3 = {round(pl.get('b3_real'),1) if pl.get('b3_real') is not None else 'n/a'}; |b3_real| percentile in placebo dist = {round(pl.get('abs_ge_real_pct',0)*100,1) if pl.get('abs_ge_real_pct') is not None else 'n/a'}%
- placebo b3 quantiles: {pl.get('quantiles')}

## Threshold sensitivity (pi_signal, Hajek cost)
{json.dumps(rob.get('threshold_sensitivity',{}),indent=1)}

## Leave-top-k ATE(H1)
{json.dumps(rob.get('leave_top_k',{}),indent=1)}

## Leave-one-repo-out ATE(H1)
{json.dumps(rob.get('leave_one_repo_out',{}),indent=1)}

## Mechanism decomposition (mean LINEDEDUP vs NO_OP)
{json.dumps(mech,indent=1)}
""")

    # CONTROLLER
    with open(os.path.join(rd,'MRT_CONFIRMATORY_CONTROLLER_VALUE.md'),'w') as f:
        f.write(f"""# MRT Confirmatory (Study 2) — Controller Policy Value

Hajek self-normalized IPW (primary) + DR cross-fit (LORO). Lower cost = better. Frozen policies.

| policy | Hajek IPW | DR-LORO |
|---|---:|---:|
| pi_keep (always NO_OP) | {round(g(ctl,'pi_keep','hajek') or 0,0)} | {round(g(ctl,'pi_keep','dr_loro') or 0,0)} |
| pi_static (always LINEDEDUP) | {round(g(ctl,'pi_static','hajek') or 0,0)} | {round(g(ctl,'pi_static','dr_loro') or 0,0)} |
| pi_signal (dup_frac>0.40) | {round(g(ctl,'pi_signal','hajek') or 0,0)} | {round(g(ctl,'pi_signal','dr_loro') or 0,0)} |

- best static (Hajek): {ctl.get('best_static_hajek')} · best static (DR): {ctl.get('best_static_dr')}
- pi_signal beats BOTH statics (Hajek): **{ctl.get('signal_beats_both_hajek')}** · (DR): **{ctl.get('signal_beats_both_dr')}**

Controller value SUPPORTED only if pi_signal beats both statics on the primary estimator with
credible uncertainty and no quality collapse. Verdict: **{v.get('SIGNAL_POLICY_VALUE')}**.
""")

    # FINAL
    with open(os.path.join(rd,'MRT_CONFIRMATORY_FINAL.md'),'w') as f:
        f.write(f"""# MRT Confirmatory (Study 2) — FINAL

Independent confirmatory replication. New tasks (not in Study-1), seed 20260702, frozen
confirmatory shim, opus-4.7 temp=0. **N = {n} randomized interventions**, {o.get('n_repos')} repos,
strata {o.get('strata')}. All numbers auto-derived from immutable artifacts.

## The nine verdicts
| verdict | result |
|---|---|
| PROTOCOL_INTEGRITY | **{v.get('PROTOCOL_INTEGRITY')}** |
| LINEDEDUP_ATE_H1 | **{v.get('LINEDEDUP_ATE_H1')}** |
| REDUNDANCY_CAUSAL_MODERATOR | **{v.get('REDUNDANCY_CAUSAL_MODERATOR')}** |
| H3_REWORK_SAFETY | **{v.get('H3_REWORK_SAFETY')}** |
| PREFIX_BYTE_PRESERVATION | **{v.get('PREFIX_BYTE_PRESERVATION')}** |
| CACHE_COST_EFFECT | **{v.get('CACHE_COST_EFFECT')}** |
| QUALITY_NONINFERIORITY | **{v.get('QUALITY_NONINFERIORITY')}** |
| SIGNAL_POLICY_VALUE | **{v.get('SIGNAL_POLICY_VALUE')}** |
| DEPLOYABLE_TRACECONTROLLER | **{v.get('DEPLOYABLE_TRACECONTROLLER')}** |

## Quality (frozen NI margin {q.get('ni_margin')})
LINEDEDUP {q.get('LINEDEDUP')} vs NO_OP {q.get('NO_OP')} resolved. Risk difference {round(q.get('risk_difference'),3) if q.get('risk_difference') is not None else 'n/a'},
Newcombe 95% CI {[round(x,3) if x is not None else None for x in q.get('newcombe_ci95',[])]}. NI met: {q.get('ni_met')}.

## Comparison to Study 1 (revealed only after Study-2 verdicts frozen)
Study 1 (N=13): moderator UNDERPOWERED/NOT_ESTABLISHED, signal policy NOT_SUPPORTED, protocol SUPPORTED.
Study 2 (N={n}): see table above. Pooling (with a study indicator) is optional future work and was
NOT performed before both studies were independently frozen.
""")
    print("wrote 5 confirmatory reports")

if __name__=='__main__': main()
