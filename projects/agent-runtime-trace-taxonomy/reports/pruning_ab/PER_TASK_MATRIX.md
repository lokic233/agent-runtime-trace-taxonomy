# Per-Task Outcome Matrix — VERIFIED (opus-4.7, golden-50, SWE-bench graded)

Full pass/regress/improve map for **all 50 tasks × 13 arms**. Nothing omitted. Source of truth: `per_task_outcomes.json`.

**Legend:** `✓`=resolved · `✗`=REGRESSION (C0 solved, method didn't) · `+`=IMPROVEMENT (C0 failed, method solved) · `·`=both-fail

**Column codes:** C0=baseline · HYB1=HYBRID1 · CMB1=COMBO1 · PROG=PROG1 · M4=obs-cap-5k · AGG3/2/1=recency w=4/8/12 · SUM1=summarize-old · CMP1=tool-compress · DD2=DEDUP2 · M6=env-log · M7=old-obs-elide

| # | task | C0 | HYB1 | CMB1 | PROG | M4 | AGG3 | AGG2 | AGG1 | SUM1 | CMP1 | DD2 | M6 | M7 | row |
|--:|------|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| 1 | `astropy__astropy-12907` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | stable |
| 2 | `astropy__astropy-14096` | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | 2✗ |
| 3 | `astropy__astropy-14309` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | stable |
| 4 | `astropy__astropy-14539` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | stable |
| 5 | `astropy__astropy-14995` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | stable |
| 6 | `astropy__astropy-7166` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | stable |
| 7 | `django__django-14493` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | stable |
| 8 | `django__django-14539` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | stable |
| 9 | `django__django-14752` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | stable |
| 10 | `django__django-14771` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | stable |
| 11 | `django__django-15380` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | stable |
| 12 | `django__django-16136` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | stable |
| 13 | `pallets__flask-5014` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | stable |
| 14 | `psf__requests-1142` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | stable |
| 15 | `pydata__xarray-2905` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | stable |
| 16 | `pydata__xarray-3305` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | stable |
| 17 | `pydata__xarray-3677` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | stable |
| 18 | `pydata__xarray-4075` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | stable |
| 19 | `pydata__xarray-6721` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | stable |
| 20 | `pydata__xarray-7233` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | stable |
| 21 | `pylint-dev__pylint-4551` | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | 12✗ |
| 22 | `pylint-dev__pylint-6386` | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | 3✗ |
| 23 | `pylint-dev__pylint-6528` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | stable |
| 24 | `pylint-dev__pylint-6903` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | stable |
| 25 | `pylint-dev__pylint-7277` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | stable |
| 26 | `pylint-dev__pylint-8898` | ✗ | · | · | · | **+** | · | · | · | · | · | · | · | · |  1+ |
| 27 | `pytest-dev__pytest-5631` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | stable |
| 28 | `pytest-dev__pytest-6197` | ✗ | **+** | **+** | **+** | **+** | **+** | **+** | **+** | **+** | **+** | **+** | **+** | **+** |  12+ |
| 29 | `pytest-dev__pytest-7324` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | stable |
| 30 | `pytest-dev__pytest-7432` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | stable |
| 31 | `pytest-dev__pytest-7490` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | stable |
| 32 | `pytest-dev__pytest-7521` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | stable |
| 33 | `scikit-learn__scikit-learn-13135` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | stable |
| 34 | `scikit-learn__scikit-learn-13328` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | stable |
| 35 | `scikit-learn__scikit-learn-13439` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | stable |
| 36 | `scikit-learn__scikit-learn-14087` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | stable |
| 37 | `scikit-learn__scikit-learn-25973` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | stable |
| 38 | `scikit-learn__scikit-learn-9288` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | stable |
| 39 | `sphinx-doc__sphinx-10466` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | stable |
| 40 | `sphinx-doc__sphinx-8459` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | stable |
| 41 | `sphinx-doc__sphinx-8638` | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✗ | ✓ | ✗ | 4✗ |
| 42 | `sphinx-doc__sphinx-9320` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | stable |
| 43 | `sphinx-doc__sphinx-9367` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | stable |
| 44 | `sphinx-doc__sphinx-9658` | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✗ | ✓ | ✗ | ✓ | ✗ | ✓ | 4✗ |
| 45 | `sympy__sympy-13091` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | 1✗ |
| 46 | `sympy__sympy-13480` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | stable |
| 47 | `sympy__sympy-14248` | ✓ | ✓ | ✓ | ✗ | ✓ | ✗ | ✓ | ✗ | ✗ | ✗ | ✓ | ✗ | ✓ | 6✗ |
| 48 | `sympy__sympy-14976` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | stable |
| 49 | `sympy__sympy-19040` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✗ | 2✗ |
| 50 | `sympy__sympy-24539` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | stable |
| | **regressions** | base | 1 | 2 | 2 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 5 | |
| | **improvements** | base | 1 | 1 | 1 | 2 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | |

**Summary:** 50 tasks total · C0 baseline resolved 48/50 · 40 tasks resolve `✓` under every method (universally stable) · 10 tasks differ on at least one method.

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

Regression risk is **concentrated, not diffuse**: 8 fragile tasks account for all regressions; 40/50 are universally safe. A runtime controller can (a) detect the canary signature (tasks where early-trajectory observations are load-bearing for a late decision) and fall back to no-pruning, while (b) applying HYBRID1 aggressively on the safe majority.