# MRT Formal — Primary Results (Step 19)

**All numbers auto-generated from** `results/pruning_ab/mrt_formal/analysis_output.json`
(events sha256[:16] `e01d167205f6eb37`). Frozen shim `df08cebcfd2b37c6`, opus-4.7 temp=0.
**N = 13 randomized interventions** (LINEDEDUP=7,
NO_OP=6), 6 repos, strata MIXED=10/HIGH=3.
0 infrastructure failures, 0 excluded. **Stopping rule met: all 18 buildable pool tasks attempted.**

> ⚠️ **This is preregistered outcome tier #4 (UNDERPOWERED).** N=13 ≪ 60-event floor. All
> estimates below are **descriptive effect sizes + CIs**, explicitly NOT significance tests.
> The power analysis established <0.20 power for the practically-relevant MDE at this N.

## Primary estimand — ITT ATE on H=1 effective cost (LINEDEDUP − NO_OP, lower=better)

| quantity | value |
|---|---|
| ATE (H=1) | **-191.8** eff-cost units |
| bootstrap 95% CI | [-3540, 3358] |
| repo-clustered 95% CI (low-resolution, 6 repos) | [-3172, 2394] |
| block-permutation p (two-sided) | 0.942 |
| mean LINEDEDUP | 6148 |
| mean NO_OP | 6339 |

The point estimate (-192) is ≈3% of the control mean —
**far smaller than its own CI half-width** (~3449). No detectable average effect.

## Secondary — ITT ATE on H=3 cumulative cost
ATE(H=3) = 468.5, 95% CI [-8649, 9064], perm p=0.935.
The H=3 sign (positive/worse) differs from H=1; both CIs dwarf the estimates. No horizon-consistent effect.

## Primary moderator — interaction b3 (centered dup_frac=0.280)
Model: `Y = b0 + b1·A + b2·S + b3·A·S` (HC0 robust SE; block FE omitted at N=13, noted).

| coef | estimate | robust SE |
|---|---:|---:|
| b0 (intercept) | 6063 | 741 |
| b1 (A = LINEDEDUP) | 573 | 1627 |
| b2 (S = redundancy) | -5617 | 3608 |
| **b3 (A×S, PRIMARY)** | **924** | **4670** |

The preregistered hypothesis was **b3 < 0** (redundancy makes LINEDEDUP more favorable).
The estimate is **b3 = 924** with SE 4670 — the **wrong sign** and a CI that
overwhelmingly spans zero. **No evidence for the moderator.**

## Interpretable CATE contrasts (secondary)

| stratum | n | CATE (LINEDEDUP−NO_OP) | 95% CI |
|---|---:|---:|---|
| HIGH_REDUNDANCY | 3 | 2932 | [-1272, 7136] |
| MIXED_REDUNDANCY | 10 | -1045 | [-4572, 3047] |
| high − mixed | | 3977 | (n=3 vs 10; not interpretable) |

Directionally the HIGH stratum CATE is **positive** (LINEDEDUP *worse* where redundancy is
highest) — opposite the hypothesis — but n=3 makes this uninformative.

## Activation / dose (reported separately from ITT)
LINEDEDUP activation rate = 1.00 (every assigned LINEDEDUP removed ≥1 line).
