# Phase 4 — Heterogeneous Treatment Effects (cost)

**Question:** Do pre-treatment trace features predict the per-task treatment effect E[cost(method)−cost(C0) | features]?

## Headline: weak, repo-confounded, underpowered signal

### CATE(cost) by dup_line_ratio (the hypothesized LINEDEDUP driver)
| dup_ratio bin | LINEDEDUP mean saving | 95% CI | GENTLE6K mean saving | n |
|---|---:|:--:|---:|:--:|
| 0–0.18 | −12.6% | [−35.3, +9.0] | −23.4% | 13 |
| 0.18–0.25 | −10.0% | [−26.2, +3.3] | −0.0% | 19 |
| 0.25–0.50 | −1.0% | [−19.6, +17.2] | −1.4% | 18 |

**Every CI spans zero.** A faint positive trend (more duplicates → less negative LINEDEDUP saving) but not significant at n≈50.

### ⚠️ Negative control FAILS (the key falsification)
dup_line_ratio predicts **GENTLE6K** saving (Spearman **+0.27**) at least as strongly as **LINEDEDUP** (+0.19) — **even though GENTLE6K does not deduplicate at all** (it caps large dumps). If dup_ratio were a causal driver of the *LINEDEDUP mechanism specifically*, it should predict LINEDEDUP >> GENTLE6K. It doesn't. → **dup_line_ratio is a proxy for general task structure (size/cost/repo), not a method-specific treatment-effect modifier.**

### Exploratory rank-correlations (NOT causal)
| feature | LINEDEDUP | GENTLE6K |
|---------|---:|---:|
| dup_line_ratio | +0.19 | +0.27 |
| largest_obs_chars | +0.02 | +0.19 |
| baseline_tokens_sent | +0.20 | +0.15 |
| n_observations | +0.27 | +0.15 |

All |ρ| ≤ 0.27 — weak, and they predict both methods similarly (general-structure proxies, not HTE modifiers).

### Leave-one-repo-out (controls the repo confound)
Within-repo Spearman(dup_ratio, LINEDEDUP saving): astropy +0.77, sphinx +0.94, **but sympy −0.37, pytest +0.03** — mean +0.26 with huge variance, n=6/repo. **Direction reverses across repos** → unreliable, repo-dependent, underpowered.

### Task-weighted vs bill-weighted (honest framing)
LINEDEDUP: **task-weighted median = −1.1%** (typical task slightly worse), **bill-weighted = +6.3%** (a few big tasks drive the aggregate). The "saving" is concentrated, not typical — a controller predicting per-task effect faces a near-zero-median signal.


## Phase 4B — Interaction regression (the mission's "key quantity")
`delta_cost ~ dup_ratio + method + dup_ratio×method` (n=98 = 2 methods × 49 tasks):
- dup_ratio coef = +10.1% (affects GENTLE6K saving)
- method=LINEDEDUP coef = −2.1%
- **INTERACTION (dup_ratio × LINEDEDUP) = −2.73%, 95% CI [−18.58, +13.41] — INCLUDES ZERO**

The interaction term is the formal test of *method-specific* effect modification. It is **indistinguishable from zero** → dup_ratio modifies LINEDEDUP's effect no differently than GENTLE6K's. The feature is a **general task-structure signal, not a method-specific treatment-effect modifier.** A controller cannot use it to choose *which* method to apply. (interaction_regression.json)

## Verdict
**HETEROGENEOUS_TREATMENT_EFFECT: PARTIALLY_SUPPORTED / UNDERPOWERED.** Heterogeneity demonstrably *exists* (oracle gap +27%, see ORACLE_GAP.md), but available pre-treatment features predict it weakly (|ρ|≤0.27), fail the negative control (predict GENTLE6K ≈ LINEDEDUP), reverse direction across repos, and have CIs spanning zero at n≈50. **Not strong enough to identify method-specific effects.**
