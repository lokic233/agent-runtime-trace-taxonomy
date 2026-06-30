# Phase 6 — Controller Preregistration (frozen before untouched validation)

## Status: preregistered, but a key precondition is NOT met

Per Phase 5, **no deployable Tier-1 trace policy beats the best static method** on development data (dup-threshold +9.3% < always-GENTLE6K +10.1%, even with in-sample tuning). The mission rule states: *"If the oracle gap is substantial but the deployable policy cannot close it, report that trace signals are insufficient."* We therefore preregister the test **but record that the development evidence does not predict a positive outcome** — running untouched validation would, on current evidence, confirm the controller does not beat best-static.

## What is frozen (would not change after seeing untouched data)
- **Methods:** C0_identity, LINEDEDUP_e4, GENTLE6K_stable (+ HYBRID1 cache-bust control, SHAM no-op control). Frozen hashes in HYBRID1_FREEZE.md + causal_data_manifest.json.
- **Deployable features:** Tier-1 only (dup_line_ratio, repeated_obs_ratio, largest/median/p90 obs chars, task_stmt_chars, repo) — NO Tier-2 leakage (baseline_calls/tokens_sent forbidden).
- **Candidate policy (frozen):** `if dup_line_ratio > 0.25 → LINEDEDUP else C0` (best dev threshold). Also evaluate `always_GENTLE6K` as the static champion to beat.
- **Quality budgets:** strict 0%, low 1%, medium 3%, high 5% aggregate quality loss (one-sided 95% upper bound).
- **Primary success criterion:** at ≥1 budget, the trace policy reduces aggregate effective cost vs BOTH always-C0 AND best-static, with quality-loss UB within budget.
- **Statistical tests:** paired bootstrap (cost), repo-clustered bootstrap, Wilson UB (quality), leave-top-3-expensive-out robustness.

## Untouched cohort design (`untouched_manifest.json`)
- 100-150 SWE-bench Verified tasks **not** in golden-50, **not** in the heldout-167 (those are now development data), repo-balanced, C0-resolvable, never inspected for selection/tuning.
- NOT YET RUN. The frozen policy + this prereg must remain unaltered before execution.

## Honest precondition flag
The development oracle gap is large (+27%) but **uncaptured by Tier-1 features** (HTE report: weak, repo-confounded, negative-control-failing). The success-CATE analysis (success_cate_repeated.json) shows even HYBRID1's mean quality effect ≈ 0 with 5/10 tasks intrinsically unstable — so the quality-budget signal is dominated by noise at this scale. **Predicted untouched outcome: DEPLOYABLE_CONTROLLER_VALUE = NOT_SUPPORTED.** We preregister anyway for completeness; running it is gated on the budget/compute justification given the negative dev evidence.

## Why we are NOT running it tonight
Running 100-150 tasks × 3-4 arms (~400-600 gradings) to confirm an already-negative dev signal is low-value vs the compute. The scientifically honest move is to report the dev-stage conclusion (controller not justified) and mark untouched validation **PENDING** rather than burn budget confirming a predicted negative. If the dev signal were positive, untouched validation would be mandatory before any claim.
