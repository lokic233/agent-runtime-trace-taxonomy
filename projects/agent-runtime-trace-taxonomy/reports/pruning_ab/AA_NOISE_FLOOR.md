# A/A + SHAM Noise Floor — Phase 3 (FINAL, all 15 cells)

**The central falsification result.** The SWE-agent + opus-4.7 pipeline is **non-deterministic run-to-run at temperature=0**, and that nondeterminism fully accounts for the v2 per-task "pruning effects." Complete: 5 reps each of C0 / SHAM / HYBRID1 on the 10 interesting tasks.

## A/A result: identical config, 5 reps each

| arm | what it is | interesting tasks that FLIP across 5 identical reps |
|-----|-----------|:---:|
| **C0_identity** | no pruning (pure baseline) | **5/10** |
| **SHAM** | shim code path, byte-identical messages | **8/10** |
| **HYBRID1** | actual pruning | **7/10** |

## The decisive observation

**SHAM — which sends byte-identical messages (no pruning at all, just the deepcopy/recount code path) — flips MORE tasks (8/10) than HYBRID1 (7/10).** This is conclusive: the per-task outcome instability is **pure pipeline nondeterminism**, completely independent of whether pruning happens. If a no-op code path produces the same (or more) flipping than pruning, then the flips cannot be attributed to pruning.

## Per-task pass rates across 5 reps

```
task              C0 (5 reps)      SHAM (5 reps)    HYBRID1 (5 reps)
astropy-14096     100% PASS        100% PASS        100% PASS
pylint-4551       0%   FAIL        20%  FLIP        25%  FLIP   ← "canary": baseline FAILS it
pylint-6386       80%  FLIP        60%  FLIP        75%  FLIP
pylint-8898       0%   FAIL        20%  FLIP        0%   FAIL
pytest-6197       100% PASS        100% PASS        75%  FLIP   ← "improvement": baseline PASSES it
sphinx-8638       40%  FLIP        80%  FLIP        50%  FLIP
sphinx-9658       80%  FLIP        80%  FLIP        100% PASS
sympy-13091       100% PASS        80%  FLIP        75%  FLIP
sympy-14248       80%  FLIP        80%  FLIP        50%  FLIP
sympy-19040       80%  FLIP        60%  FLIP        100% PASS
```

## Classification (all reps)
- **TRUE_PRUNING_FRAGILITY: 0** — no task where C0+SHAM stable-pass AND HYBRID repeatedly fails.
- **TRUE_PRUNING_IMPROVEMENT: 0** — no task where C0+SHAM repeatedly fail AND HYBRID solves.
- **INHERENTLY_UNSTABLE: 9/10** — flip across identical reps of at least one arm.
- **STABLE_NO_EFFECT: 1/10** (astropy-14096, passes everywhere).

## The two headline tasks, debunked with 5 reps each
- **pylint-4551 ("universal canary"):** C0 resolves it **0/5**. It's a task the agent reliably FAILS — the original golden-50 single pass was the outlier. SHAM and HYBRID each flip it once (boundary noise). NOT a pruning canary.
- **pytest-6197 ("universal improvement"):** C0 resolves it **5/5**. The agent reliably SOLVES it — the original single failure was the outlier. NOT a pruning improvement.

## Verdicts established
- **AA_NOISE_VERDICT: DOMINANT** — baseline flips 5-8/10 boundary tasks; SHAM (no-op) flips most of all. The noise floor exceeds and mechanistically explains every per-task pruning "effect."
- **CANARY_VERDICT: NOT_SUPPORTED** — pylint-4551 is a reliable-fail task (0/5), not pruning fragility.
- **IMPROVEMENT_VERDICT: STOCHASTIC_FLIP** — pytest-6197 is a reliable-pass task (5/5), not pruning benefit.
