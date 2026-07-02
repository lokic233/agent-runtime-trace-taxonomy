# MRT Confirmatory (Study 2) — FINAL

Independent confirmatory replication. New tasks (not in Study-1), seed 20260702, frozen
confirmatory shim, opus-4.7 temp=0. **N = 70 randomized interventions**, 11 repos,
strata {'HIGH_REDUNDANCY': 30, 'MIXED_REDUNDANCY': 40}. All numbers auto-derived from immutable artifacts.

## The nine verdicts
| verdict | result |
|---|---|
| PROTOCOL_INTEGRITY | **SUPPORTED** |
| LINEDEDUP_ATE_H1 | **UNDERPOWERED** |
| REDUNDANCY_CAUSAL_MODERATOR | **UNDERPOWERED / NOT_ESTABLISHED** |
| H3_REWORK_SAFETY | **UNDERPOWERED** |
| PREFIX_BYTE_PRESERVATION | **SUPPORTED** |
| CACHE_COST_EFFECT | **DIRECTIONAL / UNDERPOWERED** |
| QUALITY_NONINFERIORITY | **SUPPORTED** |
| SIGNAL_POLICY_VALUE | **NOT_SUPPORTED / UNDERPOWERED** |
| DEPLOYABLE_TRACECONTROLLER | **NOT_SUPPORTED** |

## Quality (frozen NI margin -0.15, preregistered before outcomes)
LINEDEDUP 27/36 vs NO_OP 21/34 resolved. Risk difference **+0.132** (LINEDEDUP resolved MORE),
Newcombe 95% CI [-0.083, 0.334]. NI met: True (lower bound -0.083 ≥ margin -0.15, clears by 0.067).
**Caveat:** the point risk-difference is positive so NI is not the binding concern, but the CI is
wide (±~0.21) — NI is met at the frozen margin, not a precise safety guarantee. This is why the
verdict pairs SUPPORTED (NI met at frozen margin) with the underpowered-precision caveat.

## Key cross-study observation (descriptive, not a pooled test)
Both estimators (Hájek + DR) now **agree** best static = pi_static (always-LINEDEDUP), resolving
Study-1's unnormalized-IPW-vs-DR discrepancy. Directionally, LINEDEDUP is cheaper (ATE H1 = -995,
LORO-stable [-1388,-749] across all 11 repos) — but the CI crosses zero at N=70, so the ATE is
UNDERPOWERED, and redundancy-gating (pi_signal) does NOT beat blanket LINEDEDUP. The moderator
interaction b3 = -261 has the hypothesized sign but is indistinguishable from placebo variation
(|b3| exceeds only ~8% of 5000 placebos; block-perm p=0.91).

## Comparison to Study 1 (revealed only after Study-2 verdicts frozen)
Study 1 (N=13): moderator UNDERPOWERED/NOT_ESTABLISHED, signal policy NOT_SUPPORTED, protocol SUPPORTED.
Study 2 (N=70): see table above. Pooling (with a study indicator) is optional future work and was
NOT performed before both studies were independently frozen.
