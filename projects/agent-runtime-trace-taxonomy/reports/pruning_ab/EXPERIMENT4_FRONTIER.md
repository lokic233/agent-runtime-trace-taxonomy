# Experiment 4 Frontier — Line-Level + Retrieval Methods (GRADED)

Literature-grounded methods (SWE-Pruner line-level skim + Headroom retrievable refs), golden-50, vs tagged C0 (46/50 resolved). **Full 50-task graded data corrects the optimistic partial numbers.**

## Verified results (LINEDEDUP, RETRIEVREF graded; others pending)

| method | overall eff-cost saving | overall raw-prompt saving | per-task median | regressions | real reg (excl. A/A noise) | call-ratio | loss_UB |
|--------|------:|------:|------:|:---:|:---:|------:|------:|
| **LINEDEDUP_e4** | **+6.3%** | **+9.9%** | −1% | 5 | **1** (sympy-24539) | 1.0 | 0.207 |
| RETRIEVREF_e4 | −4.5% | −0.4% | −7% | 1 | 1 | 1.0 | 0.092 |
| SIGNAL_e4 | (grading) | | | | | 1.15 | |
| COMBOSS_e4 | (grading) | | | | | 1.15 | |
| WINCOMBO_e4 | (grading) | | | | | | |

## Honest reading

**The partial-data numbers (+24%/+16%) were optimistic sampling** — early-completing tasks were the big savers; the full 50-task set regresses to modest. Verified:
- **LINEDEDUP: +6.3% overall effective-cost / +9.9% raw-prompt saving, drift-free (1.0× calls).** 5 apparent regressions, but **4 are A/A noise-floor flippers** (pylint-6386, sphinx-9658, sympy-14248, sympy-19040 — all proven to flip under the identity baseline); only **1 real regression** (sympy-24539). 
- **RETRIEVREF: −4.5% overall** — doesn't save on full data (the retrievable-ref overhead + occasional re-reads cancel the dump savings).

## Verdict under the regression-BUDGET framing

**LINEDEDUP_e4 is a legitimate regression-budget Pareto point: +6.3% effective-cost / +9.9% raw-prompt saving for ~1 real regression** (4 of its 5 apparent regressions are baseline noise). It is:
- **cache-stable** (content-based line dedup, no prefix rewrite)
- **drift-free** (1.0× calls — removes only already-seen lines, agent loses nothing new)
- **literature-grounded** (cross-observation line dedup, the safe core of SWE-Pruner/Headroom)

This is NOT a clean statistically-significant win (per-task median −1%, CI straddles zero; loss_UB 0.207 on raw regression count). But under a **regression-allow budget**, it offers a real ~6-10% cost saving with a single real regression — the best risk-adjusted saving found in the study, and a valid frontier point for a controller with a regression budget.

## The study-wide principle (confirmed across 25+ methods)
- **Remove REDUNDANT info (already-seen lines: LINEDEDUP) → safe, modest saving.**
- **Destroy NEEDED info (truncation: CAP/SMART/SIGNAL) → drift → cost explosion.**
- **Rewrite the prefix by recency (HYBRID1) → cache-bust → catastrophe.**
The only positive-saving methods are the content-stable, redundancy-only ones, and their ceiling is modest (~6-10%) because on a cached agent the prompt is already cheap.
