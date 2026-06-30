# Phase 1 — Action-Opportunity Event Sampling (corrects the prior selection bias)

## The fix
The prior batch selected the LARGEST observation per task → 100% active, 95% KEEP. This batch enumerates ALL observations (≥200 chars) in each C0 trajectory and assigns strata by content analysis (line-level redundancy, file-header repetition, size, novelty).

## Distribution (auto-generated, 778 events across 50 tasks)
| stratum | count | description |
|---------|------:|-------------|
| A_exact_redundancy | **253** | >40% lines are exact copies of prior content |
| E_active_dependency | 202 | <10% dup, >1000 chars — likely novel/active |
| H_control | 238 | ordinary, no clear pattern |
| F_hard_negative | 189 | 20-80% dup — mixed, contains both redundant + unique |
| C_large_output | 31 | >4000 chars — large tool dumps |

## Balance gate
| check | threshold | actual | pass? |
|-------|---:|---:|:--:|
| LINE_DEDUP-eligible (A) | ≥30 | 253 | ✅ |
| GENTLE_CAP-eligible (C) | ≥30 | 31 | ✅ |
| hard negatives (F) | present | 189 | ✅ |
| not >85% KEEP | <85% | A+F+C=61% | ✅ |

## Repo balance
pylint-dev 174, sphinx-doc 135, pytest-dev 128, sympy 104, pydata 74, django 60, astropy 45, scikit-learn 44, psf 9, pallets 5. Analysis will use repo-clustered bootstrap.

## Segment sizes
min=200, median=1018, max=16568 chars. The prior batch's median was ~12000 (only largest obs); this is the real distribution of observations encountered during SWE-agent execution.
