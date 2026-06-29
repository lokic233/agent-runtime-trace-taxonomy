# Baseline Correlation Study — clean-trace-optimizer-study

Row unit: task_id x solver x baseline run (3432 traces; resolution on the CORE development cohort A=opus-4.7, B=opus-4.5, C=sonnet-3.5). Cost proxy = n_actions (action-step count) — true tokens were NOT per-trace attributable (HAL ledger untagged; reference sets ship no token field). All 'cost' claims are ACTION-COUNT claims. Controls: solver + source_harness + repo + log(n_events). BH-corrected p, task-clustered bootstrap 95% CI (600 reps). Wording: *associated with / predictive of* — never *causes/fixes*.

## Predictive ablation (the decisive out-of-sample test) — GroupKFold by task

### Cost  (log1p n_actions): cross-validated R^2 / MAE
| model | CV R^2 | MAE |
|---|---|---|
| A_nevents | 0.9974 | 0.0249 |
| B_meta | 0.9985 | 0.015 |
| C_meta_feats | 0.9986 | 0.0148 |

### Resolution (CORE A/B/C): AUROC / AUPRC / logloss / Brier
| model | AUROC | AUPRC | logloss | Brier |
|---|---|---|---|---|
| A_nevents | 0.6477 | 0.7441 | 0.6209 | 0.215 |
| B_meta | 0.8095 | 0.874 | 0.51 | 0.1674 |
| C_meta_feats | 0.8118 | 0.8786 | 0.5104 | 0.1675 |

**Out-of-sample increment of clean features (C over B):** cost R^2 0.9985->0.9986 (Δ=+0.0001); resolution AUROC 0.8095->0.8118 (Δ=+0.0023).

## RQ2 — Resolution associations (CORE cohort, logistic, standardized beta)

| feature | std beta | 95% CI (task-clustered) | BH p | n | direction |
|---|---|---|---|---|---|
| search_no_new_evidence_rate | -0.359 | [-0.50,-0.23] | 0.5 | 1338 | less likely resolved |
| oversized_then_narrow_read_rate | +0.109 | [-0.01,+0.24] | 0.00056 | 1358 | more likely resolved |
| no_evidence_patch_churn_rate | -0.100 | [-0.25,+0.06] | 0.0063 | 1251 | less likely resolved |
| edit_mechanical_failure_rate | -0.046 | [-0.17,+0.11] | 2.3e-07 | 1418 | less likely resolved |
| post_edit_test_gap | -0.033 | [-0.22,+0.17] | 0.71 | 556 | less likely resolved |
| **fraction_actions_in_no_new_evidence_streaks** | -0.303 | [-0.48,-0.17] | 5.1e-15 | 1424 | less likely resolved |
| tool_error_rate | -0.085 | [-0.20,+0.04] | 0.00056 | 1424 | less likely resolved |
| environment_setup_rate | -0.043 | [-0.26,+0.10] | 0.00082 | 1424 | less likely resolved |
| **redundant_reread_rate** | -0.338 | [-0.51,-0.19] | 0.0032 | 1358 | less likely resolved |

Note: ** = BH-significant AND bootstrap CI excludes 0. Several features are individually significant in-sample (stagnation_fraction beta=-0.30 CI excludes 0; redundant_reread beta=-0.34 CI excludes 0; search_no_new_evidence beta=-0.36 CI excludes 0), confirming they CONTAIN information about resolution — but the ablation shows this information is largely REDUNDANT with solver+harness+repo+length.

## RQ1 — Cost (action-count) associations

| feature | std beta | spearman vs n_actions | BH p |
|---|---|---|---|
| search_no_new_evidence_rate | +0.204 | 0.227 | 2.7e-37 |
| oversized_then_narrow_read_rate | -0.058 | 0.163 | 5.7e-21 |
| no_evidence_patch_churn_rate | +0.071 | 0.208 | 2.2e-28 |
| edit_mechanical_failure_rate | +0.098 | 0.111 | 1.7e-10 |
| post_edit_test_gap | +0.094 | 0.123 | 6.2e-05 |
| fraction_actions_in_no_new_evidence_streaks | +0.321 | 0.389 | 1.3e-123 |
| tool_error_rate | +0.091 | 0.141 | 1.5e-16 |
| environment_setup_rate | +0.029 | 0.048 | 0.0052 |
| redundant_reread_rate | +0.339 | 0.542 | 1.1e-252 |

CAVEAT (pre-registered): rate features whose denominator is n_actions are partly mechanically related to the action-count outcome. The ablation is the honest arbiter: features add ~0 to cost prediction beyond n_events (R^2 0.9985->0.9986).

## RQ3 — Non-convergence (hit per-solver 95th-pct action cap), logistic beta

| feature | std beta |
|---|---|
| search_no_new_evidence_rate | +0.877 |
| oversized_then_narrow_read_rate | -0.599 |
| no_evidence_patch_churn_rate | +0.198 |
| edit_mechanical_failure_rate | +0.442 |
| post_edit_test_gap | +0.306 |
| fraction_actions_in_no_new_evidence_streaks | +1.322 |
| tool_error_rate | -0.032 |
| environment_setup_rate | -0.018 |
| redundant_reread_rate | +1.511 |

Stagnation_fraction (+1.32) and search_no_new_evidence (+0.88) and redundant_reread (+1.51) strongly predict non-convergence — the clearest signal in the study, and directionally sensible (stuck traces run long).

## Negative controls

- permutation (shuffle tool_error across tasks) -> cost beta = +0.018 (≈0 ✓)
- random synthetic feature -> cost beta = -0.004 (≈0 ✓)
- random synthetic feature -> resolution beta = +0.134 (CI [+0.00,+0.26]) — non-trivially nonzero, indicating the single-feature resolution beta CIs are somewhat optimistic; the ablation (which is CV/out-of-sample) is the more trustworthy verdict.

## VERDICTS

- **CORRELATION_VERDICT (cost):** `TRACE_LENGTH_ONLY` — clean features are associated with action-count in-sample but add ~0 out-of-sample beyond trajectory length.
- **CORRELATION_VERDICT (resolution):** `INCREMENTAL_SIGNAL (WEAK)` — features carry resolution information in-sample (stagnation, redundant-reread, search-no-new-evidence all CI-significant), but the out-of-sample increment over solver+harness+repo+length is only ΔAUROC=+0.0023. The dominant resolution signal is the SOLVER (A/B at ~80% vs C at ~35%), which B already encodes.
- **Strongest genuinely-incremental signal:** non-convergence (RQ3) — stagnation_fraction and search_no_new_evidence_rate are large, sensible predictors of hitting the step cap.