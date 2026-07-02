# MRT Study-2 — Statistical Reconciliation (CANONICAL)

**Analysis-only reconciliation of the sealed Study-2 confirmatory MRT (N=70).** No raw artifact
was modified; no new trajectory or intervention was run. Source commit `1f318871d331`.
All numbers auto-derived from `results/pruning_ab/mrt_confirmatory_reconciliation/*.json`.
Reconciliation code: `harness/pruning_ab/scripts/reconcile_mrt_study2.py`
(sha256[:12] `515708cea44f`).
Tests: **22/22 pass** (`harness/pruning_ab/tests/test_mrt_study2_reconciliation.py`).
Sealed artifacts verified UNCHANGED: **True** (17 files).

> This report supersedes the earlier Study-2 verdict wording where they conflict. It corrects
> four defects in the sealed analysis: (1) omitted block fixed effects; (2) moderator center
> recomputed from Study-2 data; (3) incomplete-block randomization inference; (4) mislabeled
> placebo "percentile". Estimand types are tagged throughout:
> SOFTWARE_INVARIANT · DESCRIPTIVE · RANDOMIZATION_INFERENCE · ASYMPTOTIC · PRIMARY · SECONDARY · POST_HOC.

## Sample (sealed)
N=70 valid randomized interventions · arms {'LINEDEDUP': 36, 'NO_OP': 34} ·
strata {'HIGH_REDUNDANCY': 30, 'MIXED_REDUNDANCY': 40} · 11 repos · 0 infra failures.

## Preregistration deviations found & repaired
1. **Block fixed effects omitted.** Sealed model was `intercept + A + S + A*S`. The prereg
   specified `alpha_block(i) + b1*A + b2*S + b3*A*S`. Reconciliation implements block FE
   (18 blocks; design rank 21, condition 8.3, dof 49).
2. **Moderator center recomputed from Study-2.** Sealed used the Study-2 sample median (0.35067);
   prereg required the frozen Study-1 available-event median (**0.3429275**). Reconciliation uses
   the frozen value. **Note (important):** b3 is algebraically invariant to the center — all three
   candidate centers give b3 = 931.6. The deviation is real but did not change the
   primary moderator parameter.
3. **Incomplete-block randomization inference.** One block (HIGH_REDUNDANCY:7) is incomplete with
   observed positions [0,1], both LINEDEDUP. The sealed permutation conditioned on the realized
   2-treated prefix (degenerate). Reconciliation draws the incomplete block's assignments from the
   full 2:2 design space (6 full outcomes -> 4 distinct observed-prefix patterns), so marginal
   propensity stays 0.5 and valid assignment variation is preserved. Observed assignment IS in the
   reconstructed space: **True**.
4. **Placebo "percentile" mislabel.** The quantity P(|placebo|>=|real|) is an upper-tail
   probability, NOT the percentile rank of the real effect. Corrected below.

## Primary moderator model (PRIMARY; block FE; frozen center 0.3429275)
| coef | estimate | classical SE | HC3 SE | repo-cluster SE |
|---|---:|---:|---:|---:|
| b1 (A=LINEDEDUP) | -968 | — | — | — |
| b2 (S) | -256 | — | — | — |
| **b3 (A×S, PRIMARY)** | **932** | 2454 | 3258 | 3332 |

b3 repo-cluster 95% CI: [-5600, 7463] — spans zero.
The classical OLS SE is labeled **classical (NOT robust)**. Hypothesis was b3<0 (redundancy makes
LINEDEDUP more favorable); the point estimate is **positive** (932) with a CI overwhelmingly
spanning zero.

### Randomization inference for b3 (RANDOMIZATION_INFERENCE, design-based)
- **Sharp null** (no unit has any effect), permute A under true design, statistic |b3|: p = **0.734**.
- **Studentized sharp** (|b3/HC3se|): p = **0.752**.
- **No-moderation null** (b3=0, effects may be constant in S), Freedman-Lane design permutation: p = **0.734**.

## Placebo analysis (corrected terminology)
Real |b3| = 932; studentized t_real = 0.286.
- **Distribution-preserving (permute observed dup_frac, global):** upper-tail P(|placebo|>=|real|) = **0.739**;
  real |b3| exceeds only **26.1%** of placebos (empirical rank). (NOT "the 26.1th percentile".)
- **Within-stratum permutation:** upper-tail = 0.679.
- **Studentized global:** upper-tail = 0.730.
- **Event-ID hash (auxiliary, does not preserve moderator support):** upper-tail = 0.752.

The real interaction is **not distinguishable** from distribution-preserving finite-sample placebo variation.

## ATE H1 (PRIMARY; lower cost better)
- Unadjusted difference in means (DESCRIPTIVE): **-995** (LINEDEDUP cheaper).
- Block-adjusted ATE: -892. Block-FE A coefficient: -968.
- SEs: classical 772 · HC3 933 · repo-cluster 778.
- Block-FE A repo-cluster 95% CI: [-2493, 556] — crosses zero.
- **Tail sensitivity (honest):** leave-top-k dim -> k=1 -702, k=3 -240, k=5 -188
  (skew 1.34, excess kurtosis 1.3). The mean estimand is influenced by
  high-cost observations; tail sensitivity does NOT invalidate randomization but the average effect is imprecise.
- Sensitivity ONLY (not primary): log-diff -0.187, trimmed10 -775,
  winsor10 -950, median-diff -1254.

## Controller policy value (Hajek PRIMARY; LORO-DR SECONDARY; lower cost better)
| policy | Hajek | DR-LORO | repo-bootstrap 95% CI (Hajek) |
|---|---:|---:|---|
| pi_keep (always NO_OP) | 6455 | 6434 | [5448, 7706] |
| **pi_static (always LINEDEDUP)** | **5460** | **5468** | [4380, 6651] |
| pi_signal (dup_frac>0.40) | 6186 | 6229 | [4924, 8031] |

- **Best static = pi_static on BOTH estimators (agree = True).**
- pi_signal − pi_static = **+726** (Hajek), CI [-248, 2005] — signal policy is WORSE.
- pi_static − pi_keep = -995 (Hajek), CI [-2044, 183].
- signal beats both statics: Hajek False / DR False.

### DR cross-fit leakage audit
own-outcome fallback used: **False** · per-policy leaks: all 0 · fallback hierarchy
['train stratum-by-arm mean', 'train arm mean', 'train global mean']. Hard assertion `held_out_outcome_fallback_count == 0` PASSES.

## Quality non-inferiority (PRIMARY marginal; frozen margin -0.15; binary resolution ONLY)
LINEDEDUP 27/36 vs NO_OP 21/34 resolved · risk difference **+0.132** ·
Newcombe 95% CI [-0.083, 0.334] · lower bound -0.083 ≥ margin -0.15
(clears by 0.067). **Prespecified marginal criterion MET.** Wilson per arm:
LINEDEDUP [0.589,0.862], NO_OP [0.450,0.761].
Scope: binary SWE-bench resolution only — NOT trajectory quality, H3 rework, rereads, or semantic
correctness. Cluster-aware precision limited (repo-aware quality inference NOT executed at this N).

## H3 / task-total (SECONDARY)
Full H=3 horizon: 61/70; truncation {'horizon3': 61, 'horizon2': 8, 'horizon1': 1, 'horizon0': 0} (by arm {'0': {'1': 0, '2': 5, '3': 29}, '1': {'1': 1, '2': 3, '3': 32}}).
H3 ATE = -501 (n=70); task-total ATE = 5647 (n=70).
Rework proxies: **NOT ESTIMABLE — reread/repeated-command detectors were not stored per ...** (NOT ESTIMABLE — not logged). Caveat: shorter horizon
may reflect unsuccessful termination, not efficiency.

## Preregistration compliance (28 items)
{'completed': 22, 'partially completed': 2, 'not executed': 2, 'not estimable': 1, 'not executed / deferred': 1}
Notable: **SHAM cohort = not executed / deferred** (mode implemented, no sealed SHAM data; no new
paid runs). **H3 rework proxies = not estimable** (not logged). **Secondary ANCOVA = partial**
(2/4 covariates logged). **Wild cluster bootstrap = not executed** (11 clusters; repo-bootstrap used).
Full table: `preregistration_compliance.json`.

## Corrected nine verdicts
| Verdict | Result | Evidence | Caveat |
|---|---|---|---|
| PROTOCOL_INTEGRITY | SUPPORTED | prefix 36/36 identical=True; NO_OP byte-identical=True; 0 infra failures; obs assignment in reconstructed space=True | software invariants + design check |
| LINEDEDUP_ATE_H1 | DIRECTIONALLY FAVORABLE / NOT PRECISELY ESTABLISHED | unadj dim=-995 (LD cheaper); block-FE A=-968; cluster CI95 [-2493, 556] crosses 0; LORO stable; tail-sensitive (leave-to | lower cost better; imprecise & tail-sensitive |
| REDUNDANCY_CAUSAL_MODERATOR | NOT ESTABLISHED / UNDERPOWERED | b3=932 (hypothesized <0), cluster CI95 [-5600, 7463] spans 0; sharp-null p=0.73; FL no-moderation p=0.73; real |b3| exce | randomization inference |
| H3_REWORK_SAFETY | UNDERPOWERED / NOT ESTABLISHED | H3 ATE=-500.89501633986947 (n_full=61); rework proxies NOT ESTIMABLE (not logged) | secondary; truncation may reflect task termination |
| PREFIX_BYTE_PRESERVATION | SUPPORTED AS A SOFTWARE INVARIANT | 36/36 LINEDEDUP prior prefixes byte-identical | deterministic invariant, not a causal estimate |
| CACHE_COST_EFFECT | DIRECTIONAL / UNDERPOWERED | cache_creation LD=1693 vs NO_OP=2312 (diff -619); randomized arm contrast, mediation NOT identified | descriptive arm contrast |
| QUALITY_NONINFERIORITY | PRESPECIFIED MARGINAL CRITERION MET; CLUSTER-AWARE PRECISION LIMITED | risk diff +0.132, Newcombe CI [-0.083,0.334], lower bound -0.083 >= margin -0.15 (clears by 0.067) | binary resolution ONLY; not broad safety |
| SIGNAL_POLICY_VALUE | NOT SUPPORTED; PI_SIGNAL DOES NOT BEAT PI_STATIC | Hajek pi_signal=6186 vs pi_static=5460 vs pi_keep=6455; best static=pi_static (Hajek) / pi_static (DR), agree=True; sign | both estimators |
| DEPLOYABLE_TRACECONTROLLER | NOT SUPPORTED | requires moderator + policy value + held-out online eval; none achieved | composite |

## What a hostile reviewer can still attack
- N=70 is a discovery-scale sample; every CI is wide and the average effect is tail-sensitive.
- Only 11 repo clusters -> cluster-robust and repo-bootstrap inference is low-resolution.
- SHAM negative control is absent; the cache-cost direction is a randomized arm contrast, not an
  identified mediated causal effect.
- Task resolution is a coarse quality proxy; broad safety is NOT established.
- H3 rework proxies were not logged, so rework safety cannot be assessed.
