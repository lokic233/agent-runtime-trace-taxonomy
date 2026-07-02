# MRT Confirmatory (Study 2) — Eligibility Audit (Part VII)

Auto-generated from `results/pruning_ab/mrt_confirmatory/eligibility_audit.json`. Measured on a
**60-task random sample of NEW SWE-bench Verified tasks** (not in golden-50/Study-1), run as plain
SWE-agent (NO intervention) through a passthrough shim; availability computed OFFLINE by
`analyze_eligibility_dryrun.py` (validated to reproduce Study-1's 13/18=72% exactly).

## Audited online availability (the key planning number)
| quantity | value |
|---|---|
| tasks sampled | 60 |
| tasks reaching availability | 31 |
| **per-task availability rate** | **51.7%** |
| total available events (all steps) | 75 |
| repos reaching availability | 11 |
| first-available dup_frac median | 0.40 |
| stratum split (first-available) | HIGH=15, MIXED=16 |

The random-Verified rate (**52%**) is lower than the golden-50 pre-selected
rate (72%), as expected — the golden-50 pool was chosen for availability.

## Pool sizing (from the audited rate, single-shot × newest-only ⟹ ≤1 event/task)
| target events | tasks needed (÷ 0.517) |
|---:|---:|
| 60 (hard floor) | 117 |
| 120 | 233 |
| 160 (precision target) | 310 |
| 200 | 388 |

## Frozen Study-2 task pool
**170 tasks across 11 repos**, expected **~88 eligible events** (above the
60-event floor; below the ~310 tasks the full precision target would require). Selection:
NEW SWE-bench Verified tasks (not in golden-50/Study-1). 60 dry-run-characterized + 110 fresh, repo-capped for diversity. NO selection on any LINEDEDUP outcome. Dry-run trajectories are audit-only; Study-2 re-randomizes.

Repo distribution: astropy=14, django=33, matplotlib=16, mwaskom=2, psf=7, pydata=14, pylint-dev=4, pytest-dev=13, scikit-learn=18, sphinx-doc=21, sympy=28.

## Honest scope statement
At 170 buildable tasks we expect **~88 eligible events** — enough to clear the hard floor
and produce a reportable confirmatory ATE with a CI half-width near the N≈88 row of the precision
grid (~21% of mean), but **short of the N=160 precision target** (which needs ~310 tasks). The
moderator test will be UNDERPOWERED by design (established pre-outcome in the power analysis). This
is declared before any Study-2 outcome and is an acceptable outcome tier.

## Dry-run trajectories are audit-only
The 60 dry-run trajectories are NO-intervention (plain SWE-agent) and are used ONLY for the availability audit. They are NOT confirmatory outcomes and will NOT be reused as Study-2 events (Study-2 requires the randomizing confirmatory shim).
