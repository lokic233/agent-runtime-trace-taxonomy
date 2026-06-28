# Bootstrap Sample Balance (Stage A1)

**Generated:** 2026-06-28 · seed=20260628 (reproducible) · build_bootstrap_manifest.py

**Selected:** 60 traces (target 60-80) from TAXONOMY-DEV models only.

## Inclusion / firewall
- **Dev solvers sampled:** solver_A (opus-4.7, live/ungraded), solver_B (opus-4.5, 79.2%), solver_C (sonnet-3.5, 33.6%).
- **solver_E (qwen-32B) EXCLUDED** — held-out firewall (must not influence taxonomy).
- **solver_D (qwen-8B)** absent (not on disk) — see holdout_policy.yaml coverage gap.
- **solver_F (opus-4.6)** excluded — capability-audit only.

## Balance by axis
| solver | n |
|---|---|
| solver_B | 22 |
| solver_C | 22 |
| solver_A | 16 |

**Outcome** (sampling-balance only; firewalled from open coders): {'unsolved': 22, 'solved': 16, 'unk': 22}
- `unk` = solver_A, the live opus-4.7 run that is not yet graded. Included for BEHAVIORAL
  diversity (open coders never see outcome anyway); its resolve status backfills at grading.

**Behavior mix** (deterministic, from search/edit/test counts): {'edit_heavy': 24, 'search_heavy': 23, 'test_heavy': 13}

**Repositories** (10): {'django': 30, 'matplotlib': 2, 'psf': 2, 'pytest-dev': 7, 'astropy': 5, 'pydata': 1, 'pylint-dev': 1, 'scikit-learn': 3, 'sphinx-doc': 4, 'sympy': 5}

**Strata covered:** 145 distinct strata across the 6 axes (outcome × token-tertile ×
length-tertile × behavior-mix × error-hi/lo × stagnation). Rare strata picked first (greedy).

## Thresholds (deterministic, computed over the dev pool)
- token tertiles: [129225.66666666667, 429839.3333333333]
- length (events) tertiles: [20.0, 36.0]
- tool-error-rate median split: 0.0
- stagnation hi (no-new-evidence streak tertile): 1.0

## Known limitations
1. **Repo skew (django 30/60):** SWE-bench Verified is django-heavy; the diversity-max sampler
   prioritized BEHAVIORAL strata over repo balance. Acceptable for open coding (we need the full
   range of waste behaviors, not repo coverage). Repo-transfer generalization is tested separately
   in the split audit, not here.
2. **solver_A ungraded:** 16/60 have unknown outcome. No effect on open coding (blind to outcome).
3. **No qwen-8B (solver_D):** the weak open-weight DEV perspective is missing; solver_C (weak closed)
   partially covers the low-capability behavior range during discovery.
4. **capability_tier null in manifest:** tier is revealed to coders via a controlled side-channel,
   not embedded in the blinded record (kept in private alias map).