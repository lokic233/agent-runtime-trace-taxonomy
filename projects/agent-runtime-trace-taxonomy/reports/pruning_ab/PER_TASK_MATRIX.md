# Per-Task Outcome Matrix — VERIFIED (opus-4.7, golden-50, SWE-bench graded)

Full pass/regress/improve map for every method × every task. Source of truth: `per_task_outcomes.json`.

**Legend:** `✓`=resolved · `✗`=REGRESSION (C0 solved, method didn't) · `+`=IMPROVEMENT (C0 failed, method solved) · `·`=both-fail

| task | C0 | HYB1 | CMB1 | PROG | M4 | AGG3 | AGG2 | AGG1 | SUM1 | CMP1 | DD2 | M6 | M7 |
|------|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| `astropy__astropy-14096` | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| `pylint-dev__pylint-4551` | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| `pylint-dev__pylint-6386` | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| `pylint-dev__pylint-8898` | ✗ | · | · | · | **+** | · | · | · | · | · | · | · | · |
| `pytest-dev__pytest-6197` | ✗ | **+** | **+** | **+** | **+** | **+** | **+** | **+** | **+** | **+** | **+** | **+** | **+** |
| `sphinx-doc__sphinx-8638` | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✗ | ✓ | ✗ |
| `sphinx-doc__sphinx-9658` | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✗ | ✓ | ✗ | ✓ | ✗ | ✓ |
| `sympy__sympy-13091` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ |
| `sympy__sympy-14248` | ✓ | ✓ | ✓ | ✗ | ✓ | ✗ | ✓ | ✗ | ✗ | ✗ | ✓ | ✗ | ✓ |
| `sympy__sympy-19040` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✗ |

*(The other 40 tasks resolve `✓` under every method — the stable core.)*

## Fragility ranking (how many of 12 methods break each task)

| task | regressed by | interpretation |
|------|:---:|------|
| `pylint-dev__pylint-4551` | 12/12 | UNIVERSAL CANARY — any context modification breaks it |
| `sympy__sympy-14248` | 6/12 | highly fragile — half of methods break it |
| `sphinx-doc__sphinx-8638` | 4/12 | fragile to obs-clearing |
| `sphinx-doc__sphinx-9658` | 4/12 | fragile to obs-clearing |
| `pylint-dev__pylint-6386` | 3/12 | moderate |
| `astropy__astropy-14096` | 2/12 | only aggressive methods |
| `sympy__sympy-19040` | 2/12 | only aggressive methods |
| `sympy__sympy-13091` | 1/12 | single-method edge case |

## Improvements (C0 baseline failed, pruning method solved)

| task | fixed by | interpretation |
|------|:---:|------|
| `pytest-dev__pytest-6197` | 12/12 | **pruning HELPS** — removing distracting context let every method find the fix |
| `pylint-dev__pylint-8898` | 1/12 | edge improvement (M4 only) |

## Controller implication

Regression risk is **concentrated, not diffuse**: 8 fragile tasks account for all regressions; 42/50 are universally safe. A runtime controller can (a) detect the canary signature (tasks where early-trajectory observations are load-bearing for a late decision) and fall back to no-pruning, while (b) applying HYBRID1 aggressively on the safe majority. This per-task map is the empirical basis for that routing policy.