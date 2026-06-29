#!/usr/bin/env python3
import json, os
import pandas as pd, numpy as np
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE)
d=json.load(open(os.path.join(ROOT,'data','correlation_results.json')))
ab=d['ablation']; neg=d['negative_controls']

def beta(r): return f"{float(r['beta']):+.3f}" if r else "n/a"
def ci(r): 
    if not r or r.get('lo') is None: return ""
    return f"[{float(r['lo']):+.2f},{float(r['hi']):+.2f}]"

L=[]
L.append("# Baseline Correlation Study — clean-trace-optimizer-study\n")
L.append("Row unit: task_id x solver x baseline run (3432 traces; resolution on the CORE development cohort "
         "A=opus-4.7, B=opus-4.5, C=sonnet-3.5). Cost proxy = n_actions (action-step count) — true tokens were "
         "NOT per-trace attributable (HAL ledger untagged; reference sets ship no token field). All 'cost' claims "
         "are ACTION-COUNT claims. Controls: solver + source_harness + repo + log(n_events). BH-corrected p, "
         "task-clustered bootstrap 95% CI (600 reps). Wording: *associated with / predictive of* — never *causes/fixes*.\n")

L.append("## Predictive ablation (the decisive out-of-sample test) — GroupKFold by task\n")
L.append("### Cost  (log1p n_actions): cross-validated R^2 / MAE")
L.append("| model | CV R^2 | MAE |")
L.append("|---|---|---|")
for k in ['A_nevents','B_meta','C_meta_feats']:
    r=ab['cost'][k]; L.append(f"| {k} | {r['cv_r2']} | {r['mae']} |")
L.append("\n### Resolution (CORE A/B/C): AUROC / AUPRC / logloss / Brier")
L.append("| model | AUROC | AUPRC | logloss | Brier |")
L.append("|---|---|---|---|---|")
for k in ['A_nevents','B_meta','C_meta_feats']:
    r=ab['resolution'][k]; L.append(f"| {k} | {r['auroc']} | {r['auprc']} | {r['logloss']} | {r['brier']} |")

dC=ab['resolution']['C_meta_feats']['auroc']; dB=ab['resolution']['B_meta']['auroc']
costC=ab['cost']['C_meta_feats']['cv_r2']; costB=ab['cost']['B_meta']['cv_r2']
L.append(f"\n**Out-of-sample increment of clean features (C over B):** cost R^2 {costB}->{costC} "
         f"(Δ={costC-costB:+.4f}); resolution AUROC {dB}->{dC} (Δ={dC-dB:+.4f}).")

L.append("\n## RQ2 — Resolution associations (CORE cohort, logistic, standardized beta)\n")
L.append("| feature | std beta | 95% CI (task-clustered) | BH p | n | direction |")
L.append("|---|---|---|---|---|---|")
for f,r in d['results']['RQ2_resolution'].items():
    sign = "less likely resolved" if float(r['beta'])<0 else "more likely resolved"
    sig = "**" if (r.get('bh_p') is not None and float(r['bh_p'])<0.05 and r.get('lo') is not None and (float(r['lo'])*float(r['hi'])>0)) else ""
    L.append(f"| {sig}{f}{sig} | {beta(r)} | {ci(r)} | {float(r.get('bh_p',1)):.2g} | {r['n']} | {sign} |")
L.append("\nNote: ** = BH-significant AND bootstrap CI excludes 0. Several features are individually "
         "significant in-sample (stagnation_fraction beta=-0.30 CI excludes 0; redundant_reread beta=-0.34 "
         "CI excludes 0; search_no_new_evidence beta=-0.36 CI excludes 0), confirming they CONTAIN information "
         "about resolution — but the ablation shows this information is largely REDUNDANT with solver+harness+repo+length.")

L.append("\n## RQ1 — Cost (action-count) associations\n")
L.append("| feature | std beta | spearman vs n_actions | BH p |")
L.append("|---|---|---|---|")
for f,r in d['results']['RQ1_cost'].items():
    L.append(f"| {f} | {beta(r)} | {r.get('spearman')} | {float(r.get('bh_p',1)):.2g} |")
L.append("\nCAVEAT (pre-registered): rate features whose denominator is n_actions are partly mechanically "
         "related to the action-count outcome. The ablation is the honest arbiter: features add ~0 to cost "
         "prediction beyond n_events (R^2 0.9985->0.9986).")

L.append("\n## RQ3 — Non-convergence (hit per-solver 95th-pct action cap), logistic beta\n")
L.append("| feature | std beta |")
L.append("|---|---|")
for f,r in d['results']['RQ3_nonconv'].items():
    if r: L.append(f"| {f} | {beta(r)} |")
L.append("\nStagnation_fraction (+1.32) and search_no_new_evidence (+0.88) and redundant_reread (+1.51) strongly "
         "predict non-convergence — the clearest signal in the study, and directionally sensible (stuck traces run long).")

L.append("\n## Negative controls\n")
L.append(f"- permutation (shuffle tool_error across tasks) -> cost beta = {float(neg['permutation_tool_error_on_cost']['beta']):+.3f} (≈0 ✓)")
L.append(f"- random synthetic feature -> cost beta = {float(neg['random_feature_on_cost']['beta']):+.3f} (≈0 ✓)")
rr=neg.get('random_feature_on_resolution')
L.append(f"- random synthetic feature -> resolution beta = {float(rr['beta']):+.3f} "
         f"(CI {ci(rr)}) — non-trivially nonzero, indicating the single-feature resolution beta CIs are somewhat "
         f"optimistic; the ablation (which is CV/out-of-sample) is the more trustworthy verdict.")

L.append("\n## VERDICTS\n")
L.append("- **CORRELATION_VERDICT (cost):** `TRACE_LENGTH_ONLY` — clean features are associated with action-count "
         "in-sample but add ~0 out-of-sample beyond trajectory length.")
L.append("- **CORRELATION_VERDICT (resolution):** `INCREMENTAL_SIGNAL (WEAK)` — features carry resolution information "
         "in-sample (stagnation, redundant-reread, search-no-new-evidence all CI-significant), but the out-of-sample "
         f"increment over solver+harness+repo+length is only ΔAUROC={dC-dB:+.4f}. The dominant resolution signal is "
         "the SOLVER (A/B at ~80% vs C at ~35%), which B already encodes.")
L.append("- **Strongest genuinely-incremental signal:** non-convergence (RQ3) — stagnation_fraction and "
         "search_no_new_evidence_rate are large, sensible predictors of hitting the step cap.")
open(os.path.join(ROOT,'reports','baseline_correlation.md'),'w').write("\n".join(L))

# effects CSV
import csv
with open(os.path.join(ROOT,'reports','baseline_correlation_effects.csv'),'w',newline='') as f:
    w=csv.writer(f); w.writerow(['rq','feature','beta','lo','hi','bh_p','spearman','n'])
    for rq in ['RQ1_cost','RQ2_resolution','RQ3_nonconv']:
        for ft,r in d['results'][rq].items():
            if r: w.writerow([rq,ft,r.get('beta'),r.get('lo'),r.get('hi'),r.get('bh_p'),r.get('spearman'),r.get('n')])
print("correlation report + effects csv written")
print("cost dR2:",round(costC-costB,4),"| resolution dAUROC:",round(dC-dB,4))
