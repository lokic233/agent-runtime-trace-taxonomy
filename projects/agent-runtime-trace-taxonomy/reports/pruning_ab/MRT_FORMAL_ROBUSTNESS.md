# MRT Formal — Robustness & Falsification (Step 20)

Auto-generated from `results/pruning_ab/mrt_formal/robustness.json`. N=13 (underpowered).

## Placebo moderator (the decisive falsification)
A **task-id-hash placebo** moderator yields interaction b3 = **11078**,
which is **larger in magnitude** than the real redundancy signal's b3 = 924.
⟹ At N=13 the redundancy "signal" is **indistinguishable from a random placebo**. This is the
cleanest statement of underpowering: noise produces a bigger apparent interaction than the signal.

## Leave-one-repo-out ATE (H=1)
- drop_pylint-dev: -1756
- drop_scikit-learn: -362
- drop_pydata: -227
- drop_sphinx-doc: 552
- drop_pytest-dev: 687
- drop_sympy: -47

The ATE **flips sign** across LORO folds (e.g. drop_pytest-dev=687 vs
drop_pylint-dev=-1756) — dominated by individual points, not a stable effect.

## Leave-top-k |H=1| ATE
- k=1: -1180
- k=3: -1474
- k=5: -495

## Threshold sensitivity (pi_signal, dup_frac cut)
| threshold | IPW cost | DR cost |
|---|---:|---:|
| 0.3 | 9248 | 5820 |
| 0.4 | 7424 | 6863 |
| 0.5 | 5656 | 5991 |

No threshold produces a signal policy that beats the best static baseline with any stability.

## Horizon sensitivity
H=1 ATE and H=3 ATE differ in sign; both CIs span zero. No horizon-consistent win — so no
"H=1 win that reverses by H=3" claim is possible (nor a win claim at all).
