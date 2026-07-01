# MRT Formal — Power Analysis (Step 10)

**Auto-generated:** `results/pruning_ab/mrt_formal/power_analysis.json` ·
`harness/pruning_ab/scripts/power_mrt_formal.py`

Variance from pre-experiment **C0 ledger** (521 calls, no new treatment outcomes examined):
H=1 effective-cost **mean ≈ 5698, SD ≈ 2136** (mid-trajectory, cache_read>10k).

## Frozen minimum practically-relevant effects
- **ATE (b1):** −570 eff-cost units (≈ 10% of mean) — a deployment-relevant saving.
- **Interaction (b3):** −2000 per unit dup_fraction — redundancy flips LINEDEDUP from mild harm
  to real help across the dup_frac range.
- **Target power:** 0.80 · **α:** 0.05 (two-sided) · 2000 sims/cell.

## Power at the practically-relevant MDE (the honest headline)

| N events | power b3=−2000 (strong-MDE) | power b3=−1000 (moderate) | power ATE b1=−570 |
|---:|---:|---:|---:|
| 20 | 0.10 | 0.08 | 0.10 |
| 40 | 0.15 | 0.08 | 0.14 |
| 60 | 0.20 | 0.08 | 0.19 |
| 120 | 0.31 | 0.11 | 0.32 |
| 200 | 0.46 | 0.15 | 0.49 |

**At the practically-relevant MDE, the study is underpowered at every feasible N.** Even N=200
gives <0.50 power. The H=1 noise (SD/mean ≈ 0.37) is large relative to a 10% effect.

## What WOULD be detectable (larger true effects)

| N | ATE b1=−2000 | ATE b1=−3000 | interaction b3=−6000 | b3=−8000 |
|---:|---:|---:|---:|---:|
| 40 | 0.84 | 0.99 | 0.66 | 0.90 |
| 60 | 0.95 | 1.00 | 0.86 | 0.97 |
| 120 | 1.00 | 1.00 | 0.99 | 1.00 |

⟹ Only a **very large** ATE (≥ −2000, ~35% of mean) or a **very strong** moderator
(b3 ≤ −6000) is detectable at the achievable N. The rescue's cache-preservation signal
(cache_creation 256 vs thousands) suggests effects *could* be large — but that is a hypothesis
the formal run tests, not an assumption.

## Pool ceiling vs floor (the binding constraint)

- **Power floor:** ≥60 eligible randomized events, ≥25/arm, ≥5 repos.
- **Pool ceiling:** single-shot × newest-only ⟹ ≤1 intervention/task ⟹ **≤18 interventions**
  from the current 18-task pool (and online availability < C0 inventory due to opus-4.7 speedups).

**⟹ The current pool cannot reach the floor.** Reaching 60 events requires ~60+ buildable
tasks with online availability — a much larger image-build campaign.

## Frozen stopping rule

Stop when **(a)** 60 eligible randomized events are reached, **OR (b)** all buildable pool
tasks have been attempted (max_attempts = pool size after image builds). **Never** stop on an
observed p-value or favorable trend.

## Verdict entering execution

**STRUCTURALLY UNDERPOWERED** for the practically-relevant interaction. The formal run will
still: (1) validate protocol integrity live; (2) report ATE + interaction as **effect-size +
CI**, explicitly not significance; (3) test the cache-preservation mechanism; (4) establish a
defensible achievable-N upper bound. This is the anticipated **outcome tier #4** unless the
true effect proves very large — which the run measures honestly either way.
