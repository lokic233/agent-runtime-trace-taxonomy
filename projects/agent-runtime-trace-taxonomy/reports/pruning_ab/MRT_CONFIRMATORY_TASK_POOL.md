# MRT Confirmatory (Study 2) — Task Pool (Part IV, FROZEN)

Auto-mirrors `results/pruning_ab/mrt_confirmatory/task_manifest.json`.

## Selection (pre-treatment only; NEW tasks)
NEW SWE-bench Verified tasks (not in golden-50/Study-1). 60 dry-run-characterized + 110 fresh, repo-capped for diversity. NO selection on any LINEDEDUP outcome. Dry-run trajectories are audit-only; Study-2 re-randomizes.

- Source: SWE-bench Verified (500) minus golden-50 = 450 candidates.
- **170 tasks** selected, **11 repos**, expected **~88 eligible events**
  at the audited 52% availability rate.
- **No task selected on any LINEDEDUP outcome.** Difficult/failing tasks are NOT excluded.
- Seed 20260702. Frozen before Study-2 outcomes.

## Repo distribution
| repo | tasks |
|---|---:|
| django | 33 |
| sympy | 28 |
| sphinx-doc | 21 |
| scikit-learn | 18 |
| matplotlib | 16 |
| astropy | 14 |
| pydata | 14 |
| pytest-dev | 13 |
| psf | 7 |
| pylint-dev | 4 |
| mwaskom | 2 |

Full task list in `task_manifest.json` (170 ids).
