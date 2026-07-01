# MRT Study 1 — Statistical Reconciliation (corrected estimators)

**Study 1 label:** *Protocol-valid, underpowered formal pilot / Study 1.*
It is **NOT** a powered confirmatory moderator or controller study.

All numbers auto-generated from immutable raw artifacts via
`harness/pruning_ab/scripts/study1_reconcile.py`. **No raw Study-1 file was modified.**

## Frozen raw hashes (SHA-256, refuse-to-rewrite)
| file | sha256 |
|---|---|
| `events.jsonl` | `e01d167205f6eb37dda1c4b2db5aa754928f231813ca007709e672f7f0d04ef2` |
| `randomization_state.jsonl` | `a1c85da51dfeae832c1e5d14e02cb6159da2b5337c48ffa1f7113d79832b31fc` |
| `task_state.jsonl` | `e7755f1d3ae3940c4de345a42684305615f3151d7123fd8efe2c6213da334ea0` |
| `task_grades.json` | `559c021d51479c2c62fcd880a37a81aeb8031cc20db09c22594923b11b256675` |
| `grade_report.json` | `1fc1400218ab126a12b9197b9c535f42e7604a54f391dbac82019776f6376b1e` |

## 1. Preregistration deviation (explicit)

> **The preregistered adjusted interaction model** (block fixed effects + pre-treatment
> covariates + repo effects) **was not estimable at N=13.** The realized analysis fit only the
> four-parameter `Y = b0 + b1·A + b2·S + b3·A·S`. **This four-parameter interaction is
> descriptive and is NOT a confirmatory test of the preregistered model.**

**Corrected moderator verdict:** `REDUNDANCY_CAUSAL_MODERATOR: UNDERPOWERED / NOT_ESTABLISHED`.
The descriptive b3 = 924 (SE 4670) has the opposite sign to the hypothesis;
**per the reconciliation rule, sign is reported descriptively only and is NOT used as substantive
evidence against the signal at N=13.**

## 2. Policy-value estimation — corrected (the IPW/DR discrepancy resolved)

The original controller table mixed an **unnormalized Horvitz–Thompson IPW**
(`mean(1{A=π}/p · Y)`) with a DR estimate. At the realized **7 LINEDEDUP / 6 NO_OP** split the
unnormalized HT mean **mechanically changes total weight across policies**, which is why it
disagreed with DR. The fix is **Hájek self-normalized IPW** `ΣwᵢYᵢ / Σwᵢ`.

| policy | unnorm HT-IPW (artifact) | **Hájek IPW (primary)** | DR cross-fit (LORO) |
|---|---:|---:|---:|
| `pi_keep` (always NO_OP)   | 5852 | 6339 | 6277 |
| `pi_static` (always LINEDEDUP) | 6620 | 6148 | 5550 |
| `pi_signal` (dup_frac>0.40) | 7424 | 6894 | 6630 |
| **best static** | pi_keep | **pi_static** | **pi_static** |

**Reconciliation:** the two *valid* estimators (Hájek IPW, DR) **agree that `pi_static` (always
LINEDEDUP) is the best static** — the old "best static = pi_keep" was an **unnormalized-IPW
finite-N artifact** and is retracted. Estimators agree on best static: **False** (unnorm disagrees; the two valid ones agree).

`V(pi_signal) − min[V(pi_keep), V(pi_static)]` (positive = signal worse), repo-clustered bootstrap CI:
- signal_minus_pi_keep__hajek_ipw: **+555** eff-cost, repo-boot 95% CI [-1589, 2854]
- signal_minus_pi_static__hajek_ipw: **+746** eff-cost, repo-boot 95% CI [-1902, 3801]
- signal_minus_pi_keep__dr_crossfit: **+353** eff-cost, repo-boot 95% CI [-1259, 2676]
- signal_minus_pi_static__dr_crossfit: **+1080** eff-cost, repo-boot 95% CI [-1702, 4763]

All differences are **positive** (pi_signal costs more) but every CI **widely spans zero**.

**Corrected verdict:** `SIGNAL_POLICY_VALUE: NOT SUPPORTED BY CURRENT POINT ESTIMATES;
CONFIRMATORY POLICY EVALUATION UNDERPOWERED.`

## 3. Placebo analysis — corrected (distribution, not a single hash)

5000 deterministic placebo moderators `SHA256(task_id|placebo|j)`, each fit under the
same descriptive interaction model:
- real |b3| percentile in placebo distribution: **91.1%** (empirical placebo p = 0.911)
- block-respecting treatment-permutation test for the real b3: **p = 0.920**

> **The real interaction is NOT distinguishable from finite-sample placebo variation.**

The earlier "a single task-id hash gave a larger coefficient ⟹ decisive falsification" framing is
**retracted**: at N=13 the placebo *distribution* shows the real |b3| is unremarkable (91st pct),
which is a statement about **lack of power**, not a decisive falsification of the signal.

## 4. Quality — corrected

LINEDEDUP 4/7 vs NO_OP 5/6 resolved. Risk difference
(LINEDEDUP − NO_OP) = **-0.26**, Newcombe 95% CI
[-0.61, 0.22].

**Corrected verdict:** `QUALITY_GUARDRAIL: UNDERPOWERED.` No preregistered non-inferiority margin
existed; **no catastrophic collapse was observed (descriptive), but non-inferiority/safety is NOT
established.** The CI spans from a large harm (−0.61) to a moderate benefit (+0.22).

## 5. Cache claims — split into two verdicts

- `PREFIX_BYTE_PRESERVATION: SUPPORTED BY SOFTWARE INVARIANT` — 7/7 LINEDEDUP interventions had
  byte-identical prior prefixes (a deterministic software property, not a statistical estimate).
- `CACHE_COST_EFFECT: DIRECTIONAL / UNDERPOWERED` — arm-level cache_creation means
  (LINEDEDUP 2471 vs NO_OP 2966) are directional only at N=13.

## 6. Preregistered analyses NOT executed / not meaningfully estimable at N=13
- SHAM negative-control cohort — **not run** (deferred to Study 2)
- event-id placebo — **not run in Study 1** (task-id placebo distribution done here)
- interaction randomization inference — **now added** (block-permutation p=0.920)
- task-total sensitivity — **not run**
- pricing sensitivity — **not run**
- block-aware policy CI — partial (repo-clustered bootstrap done; block-aware deferred)
- leave-one-repo-out policy cross-fitting — **now added** (DR is LORO cross-fit)
- fully adjusted interaction model (block FE + covariates + repo FE) — **not estimable at N=13**

## Summary of corrected Study-1 verdicts
| verdict | corrected |
|---|---|
| REDUNDANCY_CAUSAL_MODERATOR | **UNDERPOWERED / NOT_ESTABLISHED** |
| SIGNAL_POLICY_VALUE | **NOT SUPPORTED BY POINT ESTIMATES; UNDERPOWERED** |
| QUALITY_GUARDRAIL | **UNDERPOWERED** |
| PREFIX_BYTE_PRESERVATION | **SUPPORTED (software invariant)** |
| CACHE_COST_EFFECT | **DIRECTIONAL / UNDERPOWERED** |

Study 1 remains a **protocol-valid, underpowered formal pilot**. It motivates — and provides
variance/eligibility inputs for — an **independent confirmatory Study 2**.
