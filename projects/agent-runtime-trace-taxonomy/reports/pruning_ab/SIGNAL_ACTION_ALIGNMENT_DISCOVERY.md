# Signal–Action Alignment Discovery (Study-2, N=70) — EXPLORATORY

**Analysis-only** on sealed Study-2. No raw artifact modified; 17 sealed files verified unchanged.
Learning target: **B(X) = E[Y(NO_OP) − Y(LINEDEDUP) | X]** (conditional advantage of LINEDEDUP;
B>0 ⟹ LINEDEDUP cheaper). Y = effective_cost_h1 (lower better). Known propensity p=0.5.
Everything here is **EXPLORATORY at N=70** — a discovery dataset, not confirmation.

> **Headline: NO pre-treatment feature family or candidate exception policy shows stable
> incremental policy value over always-LINEDEDUP.** All candidate gains have repo-bootstrap
> CIs spanning zero; advantage calibration is non-monotonic (inverted in the extreme bin).
> This is a credible negative result.

## Method
- Feature extractor (FROZEN, deterministic regex parsers; NO LLM classifier): hash-verified
  alignment of each intervention's target tool observation (sha256[:16]==segment_hash_before),
  features from the segment + STRICTLY prior messages only. 70/70 aligned, 0 failures.
  Prohibited post-treatment variables excluded (characters_removed, output, future calls,
  resolution, post cache tokens, H3). See `feature_dictionary.json`.
- Pseudo-outcomes: leave-one-repo-out cross-fit DR, B̃ = (μ0−μ1) + (1−A)/(1−p)(Y−μ0) − A/p(Y−μ1),
  μ0/μ1 = low-capacity ridge (λ=10) trained on OTHER repos only (leakage-free). All predictions OOF.
- Mean B̃: raw 924, winsor 1-99 909,
  winsor 5-95 806 (≈ +ATE; LINEDEDUP directionally cheaper on average).

## Per-family signal–action alignment (exception policy: default LINEDEDUP, override→NO_OP when B̂<0)
| family | Spearman(B̂,B̃) | V_exc − V_static | override coverage | folds improving | beats static? |
|---|---:|---:|---:|---:|:--:|
| F1_removal | -0.29 | +1076 | 24% | 0/11 | False |
| F2_liveness | -0.18 | +269 | 17% | 0/11 | False |
| F3_recoverability | -0.09 | +435 | 33% | 0/11 | False |
| F4_cache | +0.36 | -80 | 33% | 8/11 | True |
| F5_trajectory | +0.05 | -156 | 21% | 10/11 | True |
| INT_live_recov | -0.08 | +309 | 21% | 0/11 | False |
| INT_removal_cache | +0.21 | +345 | 23% | 0/11 | False |

Negative V_exc−V_static means the exception policy is *cheaper* than always-LINEDEDUP. Two families
(F4 cache-geometry −80, F5 trajectory −156) have nominally negative point gains, but see stability.

## Advantage calibration (3 coarse bins by predicted B̂; monotonic increasing = False)
| bin | n | mean predicted B̂ | mean DR benefit B̃ | LD/NO |
|---|---:|---:|---:|---:|
| 0 | 24 | -1885 | +1615 | 8/16 |
| 1 | 23 | +1323 | +764 | 14/9 |
| 2 | 23 | +4753 | +364 | 14/9 |

**Calibration is NON-monotonic and inverted in the extreme bin:** the bin the model predicts as
*lowest* LINEDEDUP advantage (bin0, B̂ ≈ -1885) has the *highest* realized DR benefit
(B̃ ≈ +1615). The learned advantage ordering is not trustworthy — consistent with
fitting finite-sample noise at N=70.

## Candidate exception policies (≤3; all EXPLORATORY)
| candidate | features | V_exc − V_static | repo-bootstrap 95% CI | override cov | folds improving | supported? |
|---|---|---:|---|---:|---:|:--:|
| C1_cache_geometry | materialized_prefix_est,calls_so_far,segment_pos_in_context | -80 | [-1024, 1037] | 33% | 8/11 | **False** |
| C2_trajectory_state | patch_exists_prior,tests_run_prior,latest_test_failed… | -156 | [-849, 591] | 21% | 10/11 | **False** |
| C3_interpretable_rule | materialized_prefix_est,patch_exists_prior | +59 | [-50, 195] | 6% | 1/11 | **False** |

**NO candidate exception policy credibly beats always-LINEDEDUP (all CIs span zero).** any_supported = False.
C1/C2 have negative point gains but CIs spanning zero and (for C1) strong leave-top-k attenuation
(gain −80 → −568 dropping top-3, i.e. driven by a few tasks). C3 (interpretable rule) is worse (+59).

## Coverage–gain curve (union model, override when B̂ < τ)
| τ | override coverage | V − V_static |
|---:|---:|---:|
| -3000 | 7% | +222 |
| -2000 | 9% | +229 |
| -1000 | 21% | +727 |
| -500 | 31% | +641 |
| 0 | 40% | +722 |
| 500 | 40% | +722 |

No threshold yields a stable, low-coverage, high-confidence improvement over always-LINEDEDUP.

## Conclusion (exploratory)
Exact syntactic redundancy is an **opportunity signal, not an action-value signal** — confirmed.
Extending to liveness, recoverability, cache-geometry, and trajectory-state pre-treatment features
does **not** recover stable action-selection value at N=70: no family's exception policy beats
always-LINEDEDUP with credible uncertainty, and the advantage model is anti-calibrated in the tail.
The strongest permissible claim: *neither task-level observational features nor decision-level
syntactic/semantic features reliably improve over the best static transformation policy; this
motivates larger randomized datasets and direct learning of action-specific counterfactual value.*

All candidate policies are FROZEN in `candidate_exception_policies.json` for potential
independent validation (Study 3), but none currently meets the bar to preregister as a
supported controller.
