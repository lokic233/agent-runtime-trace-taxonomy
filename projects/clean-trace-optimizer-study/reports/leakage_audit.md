# Leakage & Negative-Control Audit (Phase I)

## Task leakage
- GroupKFold(task_id) split: cross-fold task leaks = 0 -> PASS.
  All traces of a task stay in one fold by construction; verified no task assigned to 2 folds.

## Future leakage (prefix features)
- T5 n_actions=5 (<=5 and <= full 20)
- prefix T5 uses only events <= cutoff -> PASS.
- No feature reads final outcome / final patch / total final token count / future config outcomes.

## Outcome independence
- Feature extractor has NO access to grade/resolved files; resolved joined post-hoc -> PASS.

## Source-access integrity
- Blocked taxonomy artifacts (per_model_opportunity.md etc.) first read by integrate_semantic_annotations.py, committed AFTER FREEZE_PHASE1.md. Incidental transcript exposure disclosed.

## Feature redundancy (are they all the same variable?)
- Max off-diagonal Spearman among 6 core features = 0.26.
- Correlation matrix:
```
                                             search_no_new_evidence_rate  oversized_then_narrow_read_rate  no_evidence_patch_churn_rate  fraction_actions_in_no_new_evidence_streaks  tool_error_rate  edit_mechanical_failure_rate
search_no_new_evidence_rate                                         1.00                             0.05                          0.08                                         0.19            -0.11                          0.04
oversized_then_narrow_read_rate                                     0.05                             1.00                          0.10                                         0.08            -0.01                          0.05
no_evidence_patch_churn_rate                                        0.08                             0.10                          1.00                                         0.03             0.03                          0.10
fraction_actions_in_no_new_evidence_streaks                         0.19                             0.08                          0.03                                         1.00            -0.01                          0.25
tool_error_rate                                                    -0.11                            -0.01                          0.03                                        -0.01             1.00                          0.26
edit_mechanical_failure_rate                                        0.04                             0.05                          0.10                                         0.25             0.26                          1.00
```
- Features are distinct (max pairwise rho = 0.26); not a single collapsed dimension.

## Negative controls (from correlation study)
- permutation + random-synthetic features -> ~0 effect on cost (PASS).
- random feature on resolution single-beta ~0.13 -> single-feature CIs optimistic; OOS ablation is the trusted verdict.

## Mismatched-intervention control
- PENDING: requires paired config outcomes. Pre-registered in intervention_analysis_plan_v1.md.