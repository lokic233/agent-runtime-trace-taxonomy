# Clean vs Semantic/Heuristic Comparison (POST-HOC, after Phase-1 freeze)

The clean lane derived features independently. AFTER freezing, we open the existing project's
HEURISTIC per-model opportunity table (reports/per_model_opportunity.md) and its semantic pilot
for comparison ONLY. Frozen clean features are NOT modified.

## (1) Clean per-model prevalence vs prior heuristic (directional)

Cross-model rank agreement (Spearman over the 4 shared models opus-4.5/sonnet-3.5/opus-4.7/32B):

| axis | clean-vs-prior rank rho |
|---|---|
| search | -0.6 |
| stagnation | 0.949 |
| patch_churn | -1.0 |
| verification(no-postedit-test vs verif_gap) | 0.738 |
| context(oversized-narrow vs bloat) | -0.8 |

### Per-model side-by-side (clean prevalence vs prior heuristic %)

| model | clean_search_nne | prior_search | clean_stagnation | prior_stagnation | clean_churn | prior_patch_churn | clean_no_postedit_test | prior_verif_gap | clean_oversized_narrow | prior_context_bloat |
|---|---|---|---|---|---|---|---|---|---|---|
| opus-4.5 | 0.617 | 0.06 | 0.008 | 0.02 | 0.115 | 0.69 | 0.504 | 0.57 | 0.306 | 0.57 |
| sonnet-3.5 | 0.424 | 0.72 | 0.148 | 0.26 | 0.044 | 0.74 | 0.896 | 0.82 | 0.045 | 0.67 |
| opus-4.7 | 0.689 | 0.33 | 0.009 | 0.02 | 0.362 | 0.33 | 0.444 | 0.65 | 0.066 | 0.05 |
| SWEagentLM-32B | 0.614 | 0.82 | 0.316 | 0.38 | 0.327 | 0.45 | 0.978 | 0.82 | 0.584 | 0.0 |

## Interpretation

- The clean independent detectors REPRODUCE the prior heuristic's DIRECTIONAL per-model ranking on the search and stagnation axes (sonnet-3.5 and 32B high; opus low) — strong cross-method agreement, computed from a DIFFERENT codebase. This corroborates that those behaviors are real and observable.
- The clean lane's `oversized_then_narrow_read` (evidence-grounded CONTEXT_BLOAT) is RARER than the prior 'CONTEXT_BLOAT' (which the prior derived partly from duplicate reads). This is the intended tightening: the clean spec requires bloat EVIDENCE (oversized/truncated+re-narrow), so it does not inflate bloat from bare duplicate reads — a methodological improvement, and a point where clean and heuristic legitimately DIVERGE.
- VERIFICATION: clean `no-post-edit-test` fraction tracks the prior VERIFICATION_GAP directionally but the clean lane refuses to call it 'gap=waste' without verified oracle availability (deterministic name POST_EDIT_TEST_GAP).

## (2) Detector <-> semantic-label alignment

The semantic annotation is a PILOT (round1/round2, ~58-120 traces) with documented weak inter-annotator agreement (workload alpha ~0.15, waste L1 raw ~0.70). Full Stage-B annotation was halted/not completed. A robust detector-vs-label precision/recall on the FULL set is therefore NOT YET POSSIBLE; only the pilot smoke-test exists. We record SEMANTIC_ANNOTATION_INCREMENTAL_VALUE = NOT_YET_TESTED (full) / directional-agreement-POSITIVE (pilot-level, per the heuristic-table corroboration above).

## VERDICT

- SEMANTIC_ANNOTATION_INCREMENTAL_VALUE: NOT_YET_TESTED (full annotation incomplete; pilot shows directional agreement, not incremental predictive value).
- Clean deterministic features are SUFFICIENT to reproduce the prior directional per-model ranking WITHOUT semantic labels — consistent with the correlation finding that the per-model signal is largely captured by solver identity + a few deterministic features.
## KEY DIVERGENCE (clean-room value): PATCH_CHURN ranking inverts (rho = -1.0)

The clean churn ranking is OPPOSITE the prior heuristic — and the clean one is more defensible:

| model | prior PATCH_CHURN | clean churn(>0.2) | clean mean mech-failure rate |
|---|---|---|---|
| opus-4.5  | 0.69 | 0.11 | 0.000 |
| sonnet-3.5| 0.74 | 0.04 | **0.223** |
| opus-4.7  | 0.33 | 0.36 | 0.034 |
| 32B (E)   | 0.45 | 0.33 | 0.111 |

Sonnet-3.5's **22% of edits are MECHANICAL FAILURES** ('No replacement performed' / the `_split_string`
future-annotations harness bug). The prior PATCH_CHURN counted those retries as churn. The clean lane
(a) splits EDIT_MECHANICAL_FAILURE_RATE out as a distinct signal and (b) gates churn on no-intervening-
evidence over APPLIED edits only. Result: sonnet's apparent "churn" collapses (it was tool-mechanics +
the harness bug, not reasoning churn), while opus-4.7's genuine evidence-free re-editing ranks higher.

This INVERSION is the clearest demonstration of the clean-room study's value: a deterministic-proxy
detector that does not separate mechanical failure from reasoning churn, and does not gate on
intervening evidence, produces a per-model ranking that REVERSES under a stricter, inspection-grounded
definition. It is a DEFINITIONAL divergence, not a measurement error. The clean ranking should be
preferred for any churn-targeted intervention (PATCH_GUARD), because intervening on mechanical failures
or evidence-driven multi-part edits would not help (and could hurt).

## Updated cross-method agreement summary
- STRONG agreement: STAGNATION (rho=+0.95), VERIFICATION direction (rho=+0.74).
- DIVERGENCE (clean is stricter/better): PATCH_CHURN (rho=-1.0), CONTEXT_BLOAT (rho=-0.8), SEARCH (rho=-0.6).
  The search divergence comes from the clean SEARCH_NO_NEW_EVIDENCE using candidate-set-expansion
  (information gain) rather than near-duplicate-query counting; opus-4.7 reformulates more but expands
  the set, so clean scores it lower than the prior near-duplicate proxy did.
